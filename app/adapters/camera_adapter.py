import cv2


class CameraAdapter:
    def open(self, source: str | int):
        if isinstance(source, str) and source.isdigit():
            source = int(source)
        return cv2.VideoCapture(source)