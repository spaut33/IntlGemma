from flask import Flask, request, jsonify
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
import time

app = Flask(__name__)

print("=" * 60)
print("🚀 Загрузка TranslateGemma-4B...")
print("=" * 60)

# Настройка устройства
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"📱 Устройство: {device}")

if torch.cuda.is_available():
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    # Оптимизации для RTX 3080
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    print("✅ TF32 оптимизации включены")

# Загрузка модели
model_id = "google/translategemma-4b-it"
print(f"📥 Загрузка модели: {model_id}")

processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    low_cpu_mem_usage=True,
)

print("✅ Модель загружена успешно!")

# Показать использование памяти
if torch.cuda.is_available():
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    print(f"💾 Использовано VRAM: {allocated:.2f} GB")

print("=" * 60)
print("🌐 API сервер готов к работе!")
print("=" * 60)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "TranslateGemma API",
        "model": "google/translategemma-4b-it",
        "status": "running",
        "endpoints": {
            "translate": "POST /translate - Перевод текста",
            "translate_image": "POST /translate-image - Перевод текста с изображения",
            "health": "GET /health - Проверка здоровья",
            "languages": "GET /languages - Список поддерживаемых языков"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    gpu_info = {}
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        gpu_info = {
            "cuda_available": True,
            "gpu_name": torch.cuda.get_device_name(0),
            "vram_used_gb": round(allocated, 2),
            "vram_total_gb": round(total, 2),
            "vram_free_gb": round(total - allocated, 2)
        }
    
    return jsonify({
        "status": "healthy",
        "model": "translategemma-4b",
        "device": device,
        "gpu": gpu_info
    })

@app.route('/languages', methods=['GET'])
def languages():
    # 55 языков, поддерживаемых TranslateGemma
    supported_languages = {
        "en": "English",
        "de": "German", 
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "cs": "Czech",
        "pl": "Polish",
        "nl": "Dutch",
        "sv": "Swedish",
        "da": "Danish",
        "no": "Norwegian",
        "fi": "Finnish",
        "tr": "Turkish",
        "el": "Greek",
        "he": "Hebrew",
        "th": "Thai",
        "vi": "Vietnamese",
        "id": "Indonesian",
        # И еще 30+ языков...
    }
    return jsonify({
        "supported_languages": supported_languages,
        "total": 55,
        "note": "Поддерживаются также региональные варианты (например, en-US, de-DE)"
    })

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        
        # Валидация входных данных
        if not data.get("text"):
            return jsonify({"error": "Поле 'text' обязательно"}), 400
        
        source_lang = data.get("source_lang", "en")
        target_lang = data.get("target_lang", "ru")
        text = data.get("text")
        
        print(f"🔄 Перевод: {source_lang} → {target_lang}")
        print(f"📝 Текст: {text[:100]}...")
        
        # Создание сообщения для модели
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_lang,
                        "target_lang_code": target_lang,
                        "text": text,
                    }
                ],
            }
        ]
        
        # Обработка входа
        start_time = time.time()
        
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(device, dtype=torch.bfloat16)
        
        input_len = len(inputs['input_ids'][0])
        
        # Генерация перевода
        with torch.inference_mode():
            generation = model.generate(
                **inputs,
                max_new_tokens=data.get("max_tokens", 200),
                do_sample=False,
                temperature=0.1,
                use_cache=True,
            )
        
        # Декодирование результата
        generation = generation[0][input_len:]
        translation = processor.decode(generation, skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        
        print(f"✅ Перевод завершен за {elapsed_time:.2f}с")
        print(f"📤 Результат: {translation[:100]}...")
        
        return jsonify({
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "model": "translategemma-4b",
            "processing_time_seconds": round(elapsed_time, 2)
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/translate-image', methods=['POST'])
def translate_image():
    try:
        data = request.json
        
        # Валидация
        if not data.get("image_url"):
            return jsonify({"error": "Поле 'image_url' обязательно"}), 400
        
        source_lang = data.get("source_lang", "en")
        target_lang = data.get("target_lang", "ru")
        image_url = data.get("image_url")
        
        print(f"🖼️  Перевод изображения: {source_lang} → {target_lang}")
        print(f"🔗 URL: {image_url}")
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source_lang_code": source_lang,
                        "target_lang_code": target_lang,
                        "url": image_url,
                    }
                ],
            }
        ]
        
        start_time = time.time()
        
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(device, dtype=torch.bfloat16)
        
        input_len = len(inputs['input_ids'][0])
        
        with torch.inference_mode():
            generation = model.generate(
                **inputs,
                max_new_tokens=data.get("max_tokens", 200),
                do_sample=False,
                use_cache=True
            )
        
        generation = generation[0][input_len:]
        translation = processor.decode(generation, skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        
        print(f"✅ Перевод изображения завершен за {elapsed_time:.2f}с")
        print(f"📤 Результат: {translation[:100]}...")
        
        return jsonify({
            "translation": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "model": "translategemma-4b",
            "processing_time_seconds": round(elapsed_time, 2)
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

