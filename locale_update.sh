#!/bin/bash

# locale_update.sh: Compile all POs and show statistics

echo "Compiling PO files to MO"
for po_file in locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        mo_file="${po_file%.po}.mo"
        echo "Compiling $po_file -> $mo_file"
        msgfmt "$po_file" -o "$mo_file"
    fi
done

echo -e "\nStatistics"
for po_file in locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        echo -e "\n$po_file:"
        echo -e "  Overall: $(msgfmt --statistics "$po_file" 2>&1)"
        
        # Extract and show statistics by context
        echo -e "  By context:"
        awk '
            /^msgctxt/ { context = $0; sub(/^msgctxt "/, "", context); sub(/"$/, "", context) }
            /^msgid/ && context { msgid = $0; sub(/^msgid "/, "", msgid); sub(/"$/, "", msgid) }
            /^msgstr/ && context && msgid {
                msgstr = $0; sub(/^msgstr "/, "", msgstr); sub(/"$/, "", msgstr)
                if (msgstr == "") {
                    untranslated[context]++
                } else {
                    translated[context]++
                }
                context = ""
                msgid = ""
            }
            END {
                for (ctx in translated) {
                    total = translated[ctx] + (untranslated[ctx] ? untranslated[ctx] : 0)
                    printf "    %s: %d/%d translated\n", ctx, translated[ctx], total
                }
                for (ctx in untranslated) {
                    if (!(ctx in translated)) {
                        printf "    %s: 0/%d translated\n", ctx, untranslated[ctx]
                    }
                }
            }
        ' "$po_file"
    fi
done

if [ -f ./messages.mo ]; then
    rm ./messages.mo
fi