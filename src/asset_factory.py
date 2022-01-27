#!usr/local/env python3
# -*- coding: utf-8 -*-

# ----------------------------------------------------- IMPORTS ----------------------------------------------------- #

from ipfshttpclient import connect
from typing import Optional, Dict, Any
from pathlib import Path
from hashlib import sha256
from json import dump


class AssetFactory:
    # ------------------------------------------------- CONSTRUCTOR ------------------------------------------------- #
    def __init__(self) -> None:
        self.__client = connect()

    # --------------------------------------------------- METHODS --------------------------------------------------- #
    def build_asset(self,
                    name: str,
                    description: str,
                    properties: Dict[str, Any],
                    debug: Optional[bool] = False
                    ) -> str:
        """
        Creates the required JSON files complying with the ARC3 format
        (see https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0003.md), stores them in IPFS and returns the
        IPFS CID of the files.
        :param name: Name of the asset.
        :param description: Brief description of the asset.
        :param properties: Arbitrary key value pairs describing the properties of the asset.
        :param debug: Flag indicating whether in debug mode.
        :return: CID of the IPFS repository.
        """
        # Creating the files
        pwd = Path.cwd()
        ipfs_dir = pwd / f'{name.replace(" ", "_")}_ipfs'
        metadata_json = ipfs_dir / 'metadata.json'
        properties_json = ipfs_dir / 'properties.json'
        if ipfs_dir.exists():
            metadata_json.unlink()
            properties_json.unlink()
        else:
            ipfs_dir.mkdir()

        # Building the properties JSON file.
        with properties_json.open(mode='w') as out_file:
            dump(properties, out_file, indent=4)

        # Building ARC3 compliant metadata JSON file.
        hasher = sha256()
        BLK_SIZE = 65536
        with properties_json.open(mode='rb') as in_file:
            buffer = in_file.read(BLK_SIZE)
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = in_file.read(BLK_SIZE)

        properties_hash = hasher.hexdigest()
        metadata = {
            'title': 'Token Metadata',
            'type': 'object',
            'properties': {
                'name': name,
                'description': description,
                'external_url': properties_json.name,
                'external_url_integrity': properties_hash,
                'external_url_mimetype': 'application/json'
            }
        }

        with metadata_json.open('w') as out_file:
            dump(metadata, out_file, indent=4)

        # Pushing directory to IPFS.
        ipfs_obj = self.__client.add(ipfs_dir)
        if not debug:
            properties_json.unlink()
            metadata_json.unlink()
            ipfs_dir.rmdir()

        return ipfs_obj[-1]['Hash']  # Taking last element because it is the root directory.
