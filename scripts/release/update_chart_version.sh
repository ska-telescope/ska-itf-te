#!/bin/bash
# $1 image value you want to replace
# $2 is the file you want to edit
#!/bin/sh

case "$(uname -sr)" in
    Darwin*)
        echo 'Mac OS X'
        sed -i "" "/^\(version: \).*/s//\1$1/" $2
    ;;
    Linux*Microsoft*)
        echo 'WSL'  # Windows Subsystem for Linux
    ;;
    Linux*)
        echo 'Linux'
        sed -i "/^\(version: \).*/s//\1$1/" $2
    ;;
    CYGWIN*|MINGW*|MINGW32*|MSYS*)
        echo 'MS Windows'
    ;;

   # Add here more strings to compare

   *)
        echo 'Other OS' 
        sed -i "/^\(version: \).*/s//\1$1/" $2
    ;;
esac
