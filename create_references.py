#!/usr/bin/env python3
"""
Скрипт для создания DINO v2 referencias из изображений
"""

from dinov2_pipeline.pipeline import DinoV2Pipeline
import os

def create_references_from_folder(image_folder, reference_name_pattern=None):
    """
    Создаёт referencias из всех .jpg и .png файлов в папке
    
    Args:
        image_folder: путь к папке с изображениями LEGO
        reference_name_pattern: как назвать referencias (по умолчанию = имя файла)
    
    Example:
        create_references_from_folder("my_photos")
        # Создаст referencias из всех .jpg/.png файлов в папке
    """
    pipeline = DinoV2Pipeline()
    
    if not os.path.exists(image_folder):
        print(f"❌ Папка не найдена: {image_folder}")
        return
    
    # Ищем все изображения
    image_files = []
    for ext in ['*.jpg', '*.png', '*.JPG', '*.PNG']:
        import glob
        image_files.extend(glob.glob(os.path.join(image_folder, ext)))
    
    if not image_files:
        print(f"❌ Изображений не найдено в {image_folder}")
        return
    
    print(f"✅ Найдено изображений: {len(image_files)}\n")
    
    # Создаём referencias
    for image_path in image_files:
        try:
            # Извлекаем имя файла без расширения
            filename = os.path.basename(image_path)
            ref_name = os.path.splitext(filename)[0]
            
            print(f"📸 Обработка: {filename} → {ref_name}")
            
            pipeline.create_reference(image_path, ref_name)
            print(f"   ✅ Успешно создано!\n")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}\n")
    
    # Список всех referencias
    refs = pipeline.list_references()
    print(f"\n📋 Всего referencias: {len(refs)}")
    for ref in refs:
        print(f"   • {ref}")


def create_single_reference():
    """
    Интерактивное создание одного референса
    """
    pipeline = DinoV2Pipeline()
    
    print("=== Создание DINO v2 Референса ===\n")
    
    image_path = input("Путь к изображению LEGO: ").strip()
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        return
    
    ref_name = input("Имя referencias (например, 'red_2x4'): ").strip()
    if not ref_name:
        ref_name = os.path.splitext(os.path.basename(image_path))[0]
    
    try:
        print(f"\n⏳ Обработка {image_path}...")
        pipeline.create_reference(image_path, ref_name)
        print(f"\n✅ Референс '{ref_name}' успешно создан!")
        print(f"   Сохранено в: dinov2_pipeline/references/{ref_name}.npz")
    except Exception as e:
        print(f"\n❌ Ошибка при создании: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        print(f"Создание referencias из папки: {folder}\n")
        create_references_from_folder(folder)
    else:
        # Интерактивный режим
        create_single_reference()
