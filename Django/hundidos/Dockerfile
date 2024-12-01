FROM python:3.8.10

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /hundidos

# Copia todos los archivos locales al contenedor
COPY . .

# Pip y las dependencias
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# Ejecuta las migraciones 
RUN python manage.py makemigrations && python manage.py migrate

# Expone el puerto en el Django se ejecutara
EXPOSE 8000

# Comando por defecto para iniciar el servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
