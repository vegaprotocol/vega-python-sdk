include .env
export

EXTERN_DIR := "./extern"

all: pull_deps build_proto

proto: build_proto black

pull_deps:
	@if [ ! -d ./extern/ ]; then mkdir ./extern/; fi
	@echo "Downloading Git dependencies into " ${EXTERN_DIR}
	@echo "Downloading Vega"
	@if [ ! -d ./extern/vega ]; then mkdir ./extern/vega; git clone https://github.com/vegaprotocol/vega ${EXTERN_DIR}/vega; fi
ifneq (${VEGA_SIM_VEGA_TAG},develop)
	@git -C ${EXTERN_DIR}/vega pull; git -C ${EXTERN_DIR}/vega checkout ${VEGA_SIM_VEGA_TAG}
else
	@git -C ${EXTERN_DIR}/vega checkout develop; git -C ${EXTERN_DIR}/vega pull
endif

build_proto: pull_deps
	@rm -rf ./vega/proto
	@mkdir ./vega/proto
	@buf generate extern/vega/protos/sources 
	@GENERATED_DIR=./vega/proto scripts/post-generate.sh

.PHONY: black
black:
	@black .
