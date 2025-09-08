Вот все возможные параметры и опции для Ollama API с пояснениями:

## 📋 Основные параметры запроса

```objectscript
Set requestObj = {
    "model": "llama2",          // (обязательный) Название модели
    "prompt": "Hello",          // (обязательный) Текст запроса
    "stream": false,            // Потоковый ответ (true/false)
    
    // Дополнительные параметры
    "format": "json",           // Формат ответа (json)
    "options": {                // Параметры модели
        // см. раздел options ниже
    },
    "template": "{{.Prompt}}",  // Шаблон для промта
    "system": "You are helpful",// Системный промт
    "context": [123, 456],      // Контекст предыдущего对话
    "raw": false,               // Игнорировать шаблоны (true/false)
    "keep_alive": "5m"         // Время хранения модели в памяти
}
```

## ⚙️ Параметры в секции `options`

```objectscript
"options": {
    // 🔢 Параметры вывода
    "num_predict": 128,         // Макс. количество токенов для генерации
    "temperature": 0.8,         // Случайность (0.0-1.0, 0.0 = детерминированный)
    "top_k": 40,                // Ограничение vocabulary (0-100)
    "top_p": 0.9,               // Nucleus sampling (0.0-1.0)
    "min_p": 0.05,              // Минимальная вероятность токена
    "typical_p": 0.95,          // Typical sampling
    
    // 🎯 Параметры повторения
    "repeat_penalty": 1.1,      // Штраф за повторения (>1.0)
    "presence_penalty": 0.0,    // Штраф за присутствие токенов
    "frequency_penalty": 0.0,   // Штраф за частоту токенов
    "repeat_last_n": 64,        // Количество последних токенов для штрафа
    "penalize_newline": false,  // Штрафовать переносы строк
    
    // ⏱️ Параметры контекста
    "num_ctx": 2048,            // Размер контекста
    "num_batch": 512,           // Размер батча
    "num_thread": 4,            // Количество потоков
    
    // 🧠 Параметры модели
    "num_gpu": 1,               // Количество GPU слоев
    "main_gpu": 0,              // Основной GPU
    "low_vram": false,          // Режим низкой памяти
    "f16_kv": true,             // 16-битные ключи/значения
    "vocab_only": false,        // Только загрузка vocabulary
    "use_mmap": true,           // Использование mmap
    "use_mlock": false,         // Блокировка модели в памяти
    
    // 📊 Специфические алгоритмы
    "mirostat": 0,              // Mirostat (0=off, 1=v1, 2=v2)
    "mirostat_tau": 5.0,        // Mirostat target entropy
    "mirostat_eta": 0.1,        // Mirostat learning rate
    
    // 🛑 Параметры остановки
    "stop": ["\n", "###"],      // Строки остановки генерации
    "tfs_z": 1.0,               // Tail-free sampling
    
    // 🔍 Параметры выборки
    "seed": 0,                  // Seed для детерминизма (0=random)
}
```

## 📝 Полный пример с всеми параметрами

```objectscript
ClassMethod CompleteOllamaRequest(prompt As %String) As %DynamicObject
{
    Set requestObj = {
        "model": "llama2",
        "prompt": (prompt),
        "stream": false,
        "format": "json",
        "system": "Ты помощник. Отвечай кратко и точно.",
        "raw": false,
        "keep_alive": "10m",
        "options": {
            // Параметры генерации
            "num_predict": 100,
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "min_p": 0.05,
            "typical_p": 0.95,
            
            // Контроль повторений
            "repeat_penalty": 1.2,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1,
            "repeat_last_n": 64,
            "penalize_newline": false,
            
            // Параметры контекста
            "num_ctx": 4096,
            "num_batch": 512,
            "num_thread": 8,
            
            // GPU/память
            "num_gpu": 2,
            "main_gpu": 0,
            "low_vram": false,
            "f16_kv": true,
            "use_mmap": true,
            "use_mlock": false,
            
            // Специфические
            "mirostat": 0,
            "mirostat_tau": 5.0,
            "mirostat_eta": 0.1,
            
            // Остановка
            "stop": ["\n", "###", "Пользователь:"],
            "tfs_z": 0.95,
            
            // Детерминизм
            "seed": 123456789
        }
    }
    
    // Выполнение запроса...
    Return ##class(Your.ClassName).ExecuteOllamaRequest(requestObj)
}
```

## 🎯 Рекомендуемые настройки для разных задач

### 1. Для классификации (без рассуждений):
```objectscript
"options": {
    "num_predict": 1,
    "temperature": 0.0,
    "top_k": 1,
    "top_p": 0.01,
    "repeat_penalty": 2.0,
    "stop": [".", "!", "?", "\n"]
}
```

### 2. Для творческого письма:
```objectscript
"options": {
    "num_predict": 500,
    "temperature": 0.9,
    "top_p": 0.95,
    "repeat_penalty": 1.1,
    "mirostat": 2
}
```

### 3. Для технических ответов:
```objectscript
"options": {
    "num_predict": 300,
    "temperature": 0.3,
    "top_p": 0.8,
    "typical_p": 0.9,
    "repeat_penalty": 1.3
}
```

## 📊 Ответ от сервера

```objectscript
Set response = {
    "model": "llama2",          // Название модели
    "created_at": "2023-12-01T12:00:00Z",
    "response": "Hello!",       // Текст ответа
    "done": true,               // Завершено ли поколение
    "context": [123, 456],      // Контекст для продолжения
    "total_duration": 500000000,// Общее время в наносекундах
    "load_duration": 100000000, // Время загрузки модели
    "prompt_eval_count": 5,     // Количество токенов в промте
    "prompt_eval_duration": 100000000,
    "eval_count": 10,           // Количество сгенерированных токенов
    "eval_duration": 300000000  // Время генерации
}
```

## ⚠️ Важные замечания

1. **Обязательные параметры**: `model` и `prompt`
2. **Температура**: `0.0` = детерминированный, `1.0` = случайный
3. **Потоковый режим**: `stream: true` для постепенного получения ответа
4. **Контекст**: Используйте `context` из ответа для продолжения диалога
5. **Память**: `keep_alive` контролирует время хранения модели в памяти

Это все основные параметры API Ollama. Настройки могут немного отличаться в зависимости от версии Ollama и конкретной модели.