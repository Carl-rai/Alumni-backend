import os

import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage


class AssetFolderCloudinaryStorage(MediaCloudinaryStorage):
    """
    Keep Django's path-based public IDs while also assigning Cloudinary
    Media Library asset folders so folders appear in the console.
    """

    def _upload(self, name, content):
        options = {
            "use_filename": True,
            "resource_type": self._get_resource_type(name),
            "tags": self.TAG,
        }
        folder = os.path.dirname(name)
        if folder:
            normalized_folder = folder.replace("\\", "/")
            options["folder"] = normalized_folder
            options["asset_folder"] = normalized_folder
        return cloudinary.uploader.upload(content, **options)
