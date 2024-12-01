FROM python:3.8.10

# Instala Chromium y sus dependencias
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configura el entorno para Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /hundidos

# Copia todos los archivos locales al contenedor
COPY . .

# Instala pip y las dependencias
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# Expone el puerto en el que se ejecutará Django
EXPOSE 8000

# Comando por defecto para iniciar el servidor
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
