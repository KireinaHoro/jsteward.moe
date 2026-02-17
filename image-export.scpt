-- AppleScript App to call blog-export on selected images
-- Place this inside Script Editor and export as Application

on open droppedItems
    my processImages(droppedItems)
end open

on processImages(theFiles)
    -- Get the directory containing this app
    set appPath to POSIX path of (path to me)
    set appDir to do shell script "dirname " & quoted form of appPath

    -- Prompt for grid size (optional)
    set gridSize to text returned of (display dialog "Enter grid size (e.g. 2x2, 3x2, 4x1) or leave blank for horizontal" default answer "")

    -- Prompt for collection name
    set collectionName to text returned of (display dialog "Enter destination collection name or leave blank for incoming" default answer "")

    -- Prompt for collection name
    set outFileName to text returned of (display dialog "Enter output file name or leave blank for timestamp" default answer "")

    -- Convert dropped items to POSIX paths
    set inputPaths to {}
    repeat with f in theFiles
        set end of inputPaths to POSIX path of f
    end repeat

    -- Build shell command
    set cmd to appDir & "/image-export.sh"

    if gridSize is not "" then
        set cmd to cmd & " -g " & gridSize
    end if

    if collectionName is not "" then
        set cmd to cmd & " -c " & collectionName
    end if

    if outFileName is not "" then
        set cmd to cmd & " -n " & outFileName
    end if

    repeat with p in inputPaths
        set cmd to cmd & " " & quoted form of p
    end repeat

    -- Run the blog-export script
    do shell script cmd
end processImages
