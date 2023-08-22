#!/usr/bin/env sh

lynx_dir=$1

if [ ! -d "${lynx_dir}/src" ]; then
  mkdir "${lynx_dir}/src"
fi

if [ ! -d "${lynx_dir}/src/lynx" ]; then
    cp -r "${lynx_dir}/lynx" "${lynx_dir}/src"
fi

if [ -f "${lynx_dir}/requirements.txt" ]; then
    rm "${lynx_dir}/requirements.txt"
fi

cp -f "data/lipidlynxx/pyproject.toml" "${lynx_dir}/pyproject.toml"
cp -f "data/lipidlynxx/setup.cfg" "${lynx_dir}/setup.cfg"
