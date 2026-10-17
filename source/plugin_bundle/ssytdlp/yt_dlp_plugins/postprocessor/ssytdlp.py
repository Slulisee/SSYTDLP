"""SSYTDLP's bundled metadata processor; no third-party plugin discovery."""
import os
from yt_dlp.postprocessor.common import PostProcessor
from yt_dlp_plugins.postprocessor._ssy_metadata import normalize_info


class SSYTDLPMetadataPP(PostProcessor):
    def __init__(self, downloader=None, prefer_flat='0'):
        super().__init__(downloader)
        self.prefer_flat = prefer_flat == '1'

    def run(self, info):
        return [], normalize_info(info, os.environ.get('SSYTDLP_MEDIA_ROOT'), self.prefer_flat)
