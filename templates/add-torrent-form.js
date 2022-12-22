function change_selected_files_spaen(file_input){
    if (file_input.files.length == 1)
        document.getElementById('selected_files').textContent = file_input.files[0].name;
    else
        document.getElementById('selected_files').textContent = file_input.files.length + " Files chosen";

  }