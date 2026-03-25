# -*- coding: utf-8 -*-
from __future__ import annotations

import cv2


def draw_detection(frame_bgr, result):
    """Нарисовать подписи и ограничивающие прямоугольники на кадре."""
    if result is None:
        return frame_bgr

    if isinstance(result, list):
        results = result
    else:
        results = [result]

    if not results:
        return frame_bgr

    output = frame_bgr.copy()

    for detection in results:
        x1, y1, x2, y2 = detection.bbox
        label = f"{detection.name} | {detection.confidence:.1f}%"

        cv2.rectangle(output, (x1, y1), (x2, y2), (40, 220, 40), 2)

        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        label_y1 = max(0, y1 - text_h - baseline - 8)
        label_y2 = label_y1 + text_h + baseline + 8
        label_x2 = x1 + text_w + 10

        cv2.rectangle(output, (x1, label_y1), (label_x2, label_y2), (40, 220, 40), -1)
        cv2.putText(
            output,
            label,
            (x1 + 5, label_y2 - baseline - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
    return output
