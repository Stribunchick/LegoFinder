# Robust Pipeline

Новый независимый пайплайн сравнения эталона и детали в кадре.

## Что делает

- строит маску эталона на однотонном фоне;
- сохраняет цвет, контур и локальные признаки;
- расширяет эталон synthetic affine-view вариантами для устойчивости к наклону и повороту;
- ищет объект в кадре через feature matching + homography;
- строит точный `bounding box` по проварпленной маске эталона, а не по грубому прямоугольнику.

## Почему это лучше под ваше ТЗ

- `Precision`: ложные срабатывания режутся несколькими независимыми проверками:
  - mutual ratio test для локальных признаков;
  - RANSAC homography;
  - coverage по площади опорных совпадений;
  - edge support;
  - masked color consistency.
- `Robustness`:
  - SIFT/AKAZE устойчивее к освещению, чем обычный шаблонный матчинг;
  - synthetic affine views помогают при изменении ракурса до умеренных наклонов;
  - RANSAC допускает частичное перекрытие объекта.

## Быстрый пример

```python
import cv2

from robust_pipeline import RobustPartMatchingPipeline

pipeline = RobustPartMatchingPipeline(storage_dir="data/robust_templates")

reference = cv2.imread("reference.jpg")
pipeline.add_reference("red_brick", reference)
pipeline.load_reference("red_brick")

frame = cv2.imread("scene.jpg")
result = pipeline.process_frame(frame, confidence_threshold=50)

if result:
    print(result.name, result.confidence, result.bbox, result.debug)
```
