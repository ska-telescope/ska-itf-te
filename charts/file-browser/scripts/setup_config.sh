set -eux
set -o pipefail

echo "Setting config: "
echo "source: ${SOURCE_CONFIG}"
echo "destination: ${DESTINATION_CONFIG}"

cp ${SOURCE_CONFIG} ${DESTINATION_CONFIG}
chmod 777 ${DESTINATION_CONFIG}

echo "Successfully set up config."
