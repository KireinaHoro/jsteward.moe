Title: Analysis of Android cryptfs
Date: 2018-05-11 13:00
Modified: 2018-05-04 13:00
Category: Android
Tags: android, gsoc, encryption
Slug: analysis-of-android-cryptfs
Status: published

## The story

I'm working on my GSoC 2018 project, and part of my work at this point is to take over `init` on an Android system. In order to get to the real root located in `/data` on Android, I need to mount the encrypted Android userdata partition, which uses Linux's `dm-crypt` target of `device-mapper`. Though I thought that it would be a pretty easy task, it turned out otherwise. In this article I analyze the routine of AOSP's `vold` decrypting the `userdata` block device.

Along the way of analyzing, I picked the necessary functions and macro definitions and trimmed unnecessary code in hope of splitting the `cryptfs` component out of Android's `vold`, which is too much an overkill for simply decrypting the `userdata` partition; what's more, it's virtually impossible to get `vold` working in the rural context of `init`, as nothing on the system has been set up yet. Unfortuately, a key component turned out to be rather hard to get, of which we'll see later on in this article. The partial work done can be found in [this repository][1].

## Find the key function

According to [Android Source][2], the entire encryption/decryption logic of Android is in `cryptfs.cpp`, a component of Android's volume manager daemon `vold`. After some rough `C-s`'ing in [the source][3], we come across the key function:

	static int test_mount_encrypted_fs(struct crypt_mnt_ftr* crypt_ftr,
                                       const char *passwd, const char *mount_point, const char *label)

But before we look at the function body, let's check the parameters first. The definition of `struct crypt_mnt_ftr` can be found in [`cryptfs.h`][4]. Telling from the name of the structure as well as some common sense of what should be needed to `test_mount` an encrypted filesystem, we can see that this structure is a __crypto footer__. As the comments in `cryptfs.h` states:

	/* This structure starts 16,384 bytes before the end of a hardware
	 * partition that is encrypted, or in a separate partition.  It's location
	 * is specified by a property set in init.<device>.rc.
	 * The structure allocates 48 bytes for a key, but the real key size is
	 * specified in the struct.  Currently, the code is hardcoded to use 128
	 * bit keys.
	 * The fields after salt are only valid in rev 1.1 and later stuctures.
	 * Obviously, the filesystem does not include the last 16 kbytes
	 * of the partition if the crypt_mnt_ftr lives at the end of the
	 * partition.
	 */

On Nexus 6P, the footer is located in the 16MB-`metadata` partition, while on Oneplus 5 this footer is located at the end of the `userdata` filesystem. To really know about where this information is, `vold` will read the device's `fstab` (usually located in the `initramfs`) with the help of `fs_mgr` to get the true location of the footer, be it an individual partition or an offset relative to the start of `userdata` partition.

## Digging deeper

Now that we know where is the information that's needed to restore the structure of the userdata partition, we can start reading the function body of `test_mount_encrypted_fs`. The first (and the only one that's important) foreign function we run into is `decrypt_master_key` [here][5], whose definition can be found [here][6]:

	static int decrypt_master_key(const char *passwd, unsigned char *decrypted_master_key,
								  struct crypt_mnt_ftr *crypt_ftr,
								  unsigned char** intermediate_key,
								  size_t* intermediate_key_size)
	{
		kdf_func kdf;
		void *kdf_params;
		int ret;
		get_kdf_func(crypt_ftr, &kdf, &kdf_params);
		ret = decrypt_master_key_aux(passwd, crypt_ftr->salt, crypt_ftr->master_key,
									 decrypted_master_key, kdf, kdf_params,
									 intermediate_key, intermediate_key_size);
		if (ret != 0) {
			SLOGW("failure decrypting master key");
		}
		return ret;
	}
	
Woah, more new friends! What comes first is `kdf_func`. After `ripgrep`'ing around, we can find that it's a `typedef` declared [here][7]:

	typedef int (*kdf_func)(const char *passwd, const unsigned char *salt,
							unsigned char *ikey, void *params);

And that `get_kdf_func` turned out to be selecting the correct Key Derivation Function that _derives_ the master key that's used for encrypting the entire `userdata` function. We'll come back to the KDF later. We can see that the real cryptographical logic is in the function `decrypt_master_key_aux` [here][8]. The code is a little bit long to include here, and it's simply a reverse of the Key Derivation process, so instead of dissecting this function here, I'll put it off until we finish the part on KDF, after which the master key decryption process would be quite straightforward.

## The nightmare--Key Derivation Function

Android system currently have three versions of the KDF, among which current Android version is using the `scrypt-keymaster` function defined [here][9]. The key derivation process is as follows:

  * Generate 16 bytes randomly as the Disk Encryption Key (DEK) and then generate 16 bytes randomly as the salt (SALT);
  * Use scrypt (`crypto_scrypt`) on the User Password-SALT pair, resulting in a hash of 32 bytes; take this as Intermediate Key 1 (IK1)
  * Pad IK1 to match the size of secret key in crypto hardware (256 bytes RSA as of now), patching scheme as follows:
	`00 || IK1 || 00..00 # one zero byte, 32 IK1 bytes, 223 zero bytes`
  * Sign IK1 with crypto hardware, resulting in 256 bytes of signature as IK2;
  * Use scrypt on the IK2-SALT pair, resulting in a hash of 32 bytes; take this as IK3;
  * Use the first 16 bytes of IK3 as Key Encryption Key (KEK, used to encrypt DEK), and the last 16 bytes as Initialization Vector (IV);
  * Use AES_CBC with KEK as secret key and IV as the initialization vector to encrypt DEK, which is the encrypted master key. Store this into the data structure `crypt_mnt_ftr`, which we discussed earlier.
  
As you may notice, the hardest part in this system to implement by hand is the __crypto hardware__, and the key function we can't handle here is `keymaster_sign_object`. Android HAL implements access to the crypto hardware by proxying actual operations to the vendor firmware blob. The high-level abstraction for the device is implemented [here][9] as a part of `vold`, while the low-level interfaces are buried in `libhardware` component of Android, which is the Android HAL. This is the point where I stopped further investigations, as further dissecting Android HAL will take reasonably longer time, with no guarantee of successfully implementing the crypto hardware signing procedure.

## What next?

So, decrypting Android `userdata` partition seems to be a no-go for now. Yet, fortunately, we can bypass the forced encryption by modifying Android's `fstab`. For Nexus 6P, the line for `userdata` reads:

	/dev/block/platform/soc.0/f9824900.sdhci/by-name/userdata     /data           ext4    noatime,nosuid,nodev,barrier=1,data=ordered,nomblk_io_submit,noauto_da_alloc,errors=panic,inode_readahead_blks=8 wait,check,forcefdeorfbe=/dev/block/platform/soc.0/f9824900.sdhci/by-name/metadata
	
Note the `forcefdeorfbe` keyword: this means that either Full-Disk Encryption (which is what we've discussed in this article) or File-Based Encryption is required on this device; if no encryption is present, the device will be encrypted by `vold` on boot. What's written after it is the location of the `crypt_mnt_ftr` structure we discussed above. 

To bypass the forced encryption, we simply substitute `forcedfdeorfbe` with `encryptable` and formatting the `userdata` partition. In this way `userdata` will remain unencrypted. I'll leave encryption as something to encypt later, maybe with LUKS, which is something far easier to use in the GNU/Linux land.

[1]: https://github.com/KireinaHoro/preinit_angler
[2]: https://source.android.com/security/encryption/full-disk
[3]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp
[4]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.h#98
[5]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp#1610
[6]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp#1253
[7]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.h#230
[8]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp#1188
[9]: https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp#1062
