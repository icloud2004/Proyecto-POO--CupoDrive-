Comando    Descripción
git status    Muestra el estado actual: qué archivos han cambiado, nuevos, o están listos para commit.
git add <archivo>    Agrega un archivo específico al área de preparación (staging).
git add .    Agrega todos los archivos modificados o nuevos.
git reset <archivo>    Quita un archivo del área de preparación sin borrar los cambios.
git diff    Muestra diferencias entre el archivo modificado y el último commit.
💾 4️⃣ GUARDAR CAMBIOS LOCALMENTE
Comando    Descripción
git commit -m "mensaje"    Crea un punto de guardado (commit) con descripción.
git commit -am "mensaje"    Agrega y commitea todos los archivos modificados de una vez.
git log    Muestra el historial de commits (autor, fecha, mensaje).
git log --oneline    Muestra el historial resumido en una sola línea por commit.
☁️ 5️⃣ SINCRONIZAR CON GITHUB
Comando    Descripción
git pull origin main    Descarga los cambios del repositorio remoto.
git pull origin main --rebase    Igual que el anterior, pero evita commits duplicados.
git push origin main    Sube tus cambios al repositorio remoto.
git fetch    Descarga los cambios remotos sin mezclarlos aún.
git merge origin/main    Fusiona los cambios descargados con tu rama actual.
🌿 6️⃣ TRABAJAR CON RAMAS (branches)
Comando    Descripción
git branch    Muestra todas las ramas locales.
git branch <nombre>    Crea una nueva rama.
git checkout <nombre>    Cambia a otra rama.
git checkout -b <nombre>    Crea una nueva rama y cambia a ella.
git merge <rama>    Fusiona otra rama con la actual.
git branch -d <nombre>    Elimina una rama local.
🧹 7️⃣ MANEJO DE ERRORES Y REVERSIONES
Comando    Descripción
git stash    Guarda temporalmente tus cambios sin hacer commit.
git stash pop    Recupera los cambios guardados con stash.
git restore <archivo>    Restaura un archivo al último commit guardado.
git revert <id_commit>    Crea un nuevo commit que revierte uno anterior.
git reset --hard <id_commit>    Vuelve el proyecto a un commit anterior (⚠️ destruye cambios locales).
git clean -fd    Elimina archivos no rastreados (no incluidos en Git).
👥 8️⃣ COLABORACIÓN Y EQUIPO
Comando    Descripción
git pull origin main    Trae los cambios de tus compañeros.
git push origin main    Sube tus cambios.
git fetch    Mira si hay actualizaciones antes de hacer pull.
git log --oneline --graph --all    Visualiza el historial de ramas y merges en forma de árbol.
🧰 9️⃣ COMANDOS ÚTILES ADICIONALES
Comando    Descripción
git show <id_commit>    Muestra detalles de un commit específico.
git shortlog    Muestra cuántos commits ha hecho cada colaborador.
git blame <archivo>    Muestra quién cambió cada línea de un archivo.
git tag <nombre>    Crea una etiqueta (por ejemplo, una versión: v1.0).
git reflog    Muestra todos los movimientos realizados (ideal para recuperar commits borrados).
'''