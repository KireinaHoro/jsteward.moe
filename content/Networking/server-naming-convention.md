Title: Server naming convention
Date: 2017-11-18 1:00
Modified: 2017-11-18 1:00
Category: Networking
Tags: networking
Slug: server-naming-convention
Status: published

## Preface

With a bunch of servers, it's necessary that they're named in a consistent manner. This article describes how the
machines should be named.

## Basic rule

A machine name should consist of the following three parts:

 - a unique identifier for the machine (Romaji of Japanese words in one Kanji, examples are given below)
 - the name of the ISP (e.g. `vultr` or `linode`)
 - the IATA code of the geographically closest airport (e.g. `hnd` for machines in Tokyo)

## Examples for the Japanese words to be chosen

    光(hikari)  影(kage)    日(hi)      月(tsuki)   雨(ame)     雪(yuki)    風(kaze)    嵐(arashi)
    海(umi)     川(kawa)    山(yama)    空(sora)    森(mori)    池(ike)     滝(taki)    島(shima)
    関(seki)    原(hara)    牧(maki)    崎(saki)    谷(tani)    岩(iwa)     垣(kaki)    塵(chiri)
    岳(take)    稲(ina)     天(ama)     埴(hani)    堀(hori)    浜(hama)    浦(ura)     沢(sawa)

## DNS rule for machines

Every machine should have A and AAAA (if any) records corresponding their **full** name under the `jsteward.moe` domain, as well as CNAME records for
their unique identifier for ease of access. The `dig` result for `hikari.pku.pek` is listed below as an example.

    ; <<>> DiG 9.11.2 <<>> hikari.jsteward.moe
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 48767
    ;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

    ;; OPT PSEUDOSECTION:
    ; EDNS: version: 0, flags:; udp: 4096
    ; COOKIE: 6098f5d0466d72b4a19210815a0fbc9fecbc66d47b912c6a (good)
    ;; QUESTION SECTION:
    ;hikari.jsteward.moe.		IN	A

    ;; ANSWER SECTION:
    hikari.JSTEWARD.moe.	185	IN	CNAME	hikari.pku.pek.jsteward.moe.
    hikari.pku.pek.JSTEWARD.moe. 185 IN	A	222.29.47.177

    ;; Query time: 2 msec
    ;; SERVER: 101.6.6.6#53(101.6.6.6)
    ;; WHEN: 土 11月 18 12:52:46 CST 2017
    ;; MSG SIZE  rcvd: 152

Application domain names (e.g. `archive.jsteward.moe`) should be pointed to the short CNAME record (e.g. `hikari.jsteward.moe`).
