#!/bin/sh

# TODO végpontok fixálása kizippelés test

LOGFILE=./assets/logs/rpi.log

zero_config() {
    while true
    do
        backend_ip=$(jq .backend.ip ./lib/config/rpi.config | sed 's/"//' | sed 's/"//')
        backend_port=$(jq .backend.port ./lib/config/rpi.config | sed 's/"//' | sed 's/"//')
        code_version_local=$(jq .code_version ./lib/config/rpi.config | sed 's/"//' | sed 's/"//')
        code_version_remote=$(curl -X GET -G http://$backend_ip:$backend_port/api/v1/files/code.zip/version | jq -r '.versionNum')
        model_version_local=$(jq .model_version ./lib/config/rpi.config | sed 's/"//' | sed 's/"//')
        model_version_remote=$(curl -X GET -G http://$backend_ip:$backend_port/api/v1/files/model.tflite/version | jq -r '.versionNum')


        if [ "$code_version_remote" = "" ]; then
            echo "Server not available"
            sleep 5
        else
            echo "Backend ip:" $backend_ip
            echo "Backend port:" $backend_port
            echo "Local code version:" $code_version_local
            echo "Remote code version:" $code_version_remote
            echo "Local model version:" $model_version_local
            echo "Remote model version:" $model_version_remote

            if [ "$code_version_local" = "$code_version_remote" ]; then
                echo "Code up to date"
            else
                echo "New code version available. Downloading..."
                wget http://$backend_ip:$backend_port/api/v1/files/code.zip/download -O ./assets/code.zip
                unzip -o assets/code.zip -d ./

                tmp=$(mktemp)
                jq '.code_version = "'$code_version_remote'"' ./lib/config/rpi.config > "$tmp" && mv "$tmp" ./lib/config/rpi.config
                echo "Code up to date"
            fi

            if [ "$model_version_local" = "$model_version_remote" ]; then
                echo "Model up to date"
            else
                echo "New model version available. Downloading..."
                wget http://$backend_ip:$backend_port/api/v1/files/model.tflite/download -O ./assets/model.tflite

                tmp=$(mktemp)
                jq '.model_version = "'$model_version_remote'"' ./lib/config/rpi.config > "$tmp" && mv "$tmp" ./lib/config/rpi.config
                echo "Model up to date"
            fi
            break
        fi
    done
 }

zero_config | tee -a ${LOGFILE}

#python3 main.py