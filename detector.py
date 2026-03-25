import cv2
import numpy as np

from new_pipeline.preprocessing import resize_keep_aspect, compute_hsv_hist, safe_gray


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


class LegoDetector:
    def __init__(self):
        self.orb = cv2.ORB_create(
            nfeatures=2000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=15,
            patchSize=31,
            fastThreshold=10
        )
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.prev_bbox = None

    def detect(self, frame_bgr, template, confidence_threshold=70):
        """
        Возвращает словарь с результатом или None.
        confidence_threshold: 0..100
        """
        if frame_bgr is None or template is None:
            return None

        frame_small, scale = resize_keep_aspect(frame_bgr, max_side=960)
        gray = safe_gray(frame_small)

        kp_frame, des_frame = self.orb.detectAndCompute(gray, None)
        if des_frame is None or len(kp_frame) < 20:
            return None

        kp_tpl = template["keypoints"]
        des_tpl = template["descriptors"]

        if des_tpl is None or len(kp_tpl) < 10:
            return None

        knn_matches = self.matcher.knnMatch(des_tpl, des_frame, k=2)

        good_matches = []
        for pair in knn_matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        if len(good_matches) < 12:
            return None

        src_pts = np.float32([kp_tpl[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        H, inlier_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if H is None or inlier_mask is None:
            return None

        inliers = int(inlier_mask.sum())
        inlier_ratio = inliers / max(1, len(good_matches))

        if inliers < 8 or inlier_ratio < 0.35:
            return None

        tpl_h = template["height"]
        tpl_w = template["width"]

        corners = np.float32(
            [[0, 0], [tpl_w, 0], [tpl_w, tpl_h], [0, tpl_h]]
        ).reshape(-1, 1, 2)

        projected = cv2.perspectiveTransform(corners, H)

        if not self._is_valid_polygon(projected, frame_small.shape):
            return None

        x, y, w, h = cv2.boundingRect(projected.astype(np.int32))
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame_small.shape[1], x + w)
        y2 = min(frame_small.shape[0], y + h)

        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame_small[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        roi_hist = compute_hsv_hist(roi)
        color_score = self._hist_similarity(template["hist"], roi_hist)
        geom_score = self._geometry_score(projected)
        match_score = self._match_score(inliers, len(kp_tpl))
        stability_score = self._stability_score((x1, y1, x2, y2))

        confidence = (
            0.35 * match_score +
            0.30 * clamp01(inlier_ratio) +
            0.15 * geom_score +
            0.15 * color_score +
            0.05 * stability_score
        ) * 100.0

        confidence = round(confidence, 1)

        if confidence < float(confidence_threshold):
            return None

        self.prev_bbox = (x1, y1, x2, y2)

        projected_full = projected / scale

        fx1 = int(np.min(projected_full[:, 0, 0]))
        fy1 = int(np.min(projected_full[:, 0, 1]))
        fx2 = int(np.max(projected_full[:, 0, 0]))
        fy2 = int(np.max(projected_full[:, 0, 1]))

        return {
            "name": template["name"],
            "confidence": confidence,
            "bbox": [fx1, fy1, fx2, fy2],
            "polygon": projected_full.astype(int),
            "debug": {
                "good_matches": len(good_matches),
                "inliers": inliers,
                "inlier_ratio": round(inlier_ratio, 3),
                "match_score": round(match_score, 3),
                "geom_score": round(geom_score, 3),
                "color_score": round(color_score, 3),
                "stability_score": round(stability_score, 3),
            }
        }

    def reset_tracking(self):
        self.prev_bbox = None

    def _hist_similarity(self, hist1, hist2):
        score = cv2.compareHist(
            hist1.astype(np.float32),
            hist2.astype(np.float32),
            cv2.HISTCMP_CORREL
        )
        return clamp01((score + 1.0) / 2.0)

    def _match_score(self, inliers, total_template_kp):
        denom = max(25, int(total_template_kp * 0.35))
        return clamp01(inliers / denom)

    def _geometry_score(self, polygon):
        pts = polygon.reshape(-1, 2).astype(np.float32)

        area = cv2.contourArea(pts)
        if area < 400:
            return 0.0

        edges = []
        for i in range(4):
            p1 = pts[i]
            p2 = pts[(i + 1) % 4]
            edges.append(np.linalg.norm(p2 - p1))

        min_edge = min(edges)
        max_edge = max(edges)

        if min_edge < 8 or max_edge <= 0:
            return 0.0

        ratio = min_edge / max_edge
        return clamp01(0.5 + 0.5 * ratio)

    def _is_valid_polygon(self, polygon, frame_shape):
        pts = polygon.reshape(-1, 2).astype(np.float32)

        area = cv2.contourArea(pts)
        if area < 400:
            return False

        h, w = frame_shape[:2]

        xs = pts[:, 0]
        ys = pts[:, 1]

        if np.max(xs) < 0 or np.max(ys) < 0:
            return False
        if np.min(xs) > w or np.min(ys) > h:
            return False

        x1, y1, bw, bh = cv2.boundingRect(pts.astype(np.int32))
        if bw < 15 or bh < 15:
            return False

        return True

    def _stability_score(self, current_bbox):
        if self.prev_bbox is None:
            return 0.5

        ax1, ay1, ax2, ay2 = self.prev_bbox
        bx1, by1, bx2, by2 = current_bbox

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
        area_b = max(1, (bx2 - bx1) * (by2 - by1))
        union = max(1, area_a + area_b - inter_area)

        iou = inter_area / union
        return clamp01(iou)