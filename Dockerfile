# Usa una imagen base de Python 3.11
FROM python:3.11-slim

# Instala git y otras dependencias necesarias (como build-essential para compilar paquetes)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos los archivos del proyecto al directorio de trabajo
COPY . .

# Comando para ejecutar el programa
CMD ["python", "bot.py"]