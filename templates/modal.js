document.addEventListener('DOMContentLoaded', () => {
    // Functions to open and close a modal
    function openModal($el) {
      $el.classList.add('is-active');
    }
  
    function closeModal($el) {
      $el.classList.remove('is-active');
    }
  
    function closeAllModals() {
      (document.querySelectorAll('.modal') || []).forEach(($modal) => {
        closeModal($modal);
      });
    }
  
    // Add a click event on buttons to open a specific modal
    (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
      const modal = $trigger.dataset.target;
      const $target = document.getElementById(modal);
  
      $trigger.addEventListener('click', () => {
        fetch_from_server().then(() => openModal($target));
      })

    });
  
    // Add a click event on various child elements to close the parent modal
    (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
      const $target = $close.closest('.modal');
  
      $close.addEventListener('click', () => {
        closeModal($target);
      });
    });
  
    // Add a keyboard event to close all modals
    document.addEventListener('keydown', (event) => {
      const e = event || window.event;
  
      if (e === 27) { // Escape key
        closeAllModals();
      }
    });

  });


  function humanFileSize(bytes, si=true) {
    const thresh = si ? 1000 : 1024;
    const units = si ? ['KB', 'MB']
                     : ['KiB', 'MiB'];
    let u = -1;
    do {
      bytes /= thresh;
      ++u;
    } while (bytes >= thresh && u < units.length - 1);
    return [Math.round(bytes * 10) / 10, units[u]];
  }

  function fromHumanFileSize(humanSize) {
    // Split the string into the number and the unit
    const [numString, unit] = humanSize.split(/\s/);
    const num = parseFloat(numString);
  
    // Look up the conversion factor for the unit
    let factor = 1;
    switch (unit) {
      case 'B': factor = Math.pow(10, 0); break;
      case 'KB': factor = Math.pow(10, 3); break;
      case 'MB': factor = Math.pow(10, 6); break;
      case 'KiB': factor = Math.pow(2, 10); break;
      case 'MiB': factor = Math.pow(2, 20); break;
    }
  
    // Return the number of bytes
    return num * factor;
  }


function fetch_from_server(){
  fetch('http://127.0.0.1:12345/edit_settings',
  {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(resp => resp.json())
  .then(jsoned_resp => {
  document.getElementById('defaultdownloadPath').value = jsoned_resp['default_download_path'];
  document.getElementById('defaultArchivePath').value = jsoned_resp['default_file_archive_path'];
  document.getElementById('port').value = jsoned_resp['port'];
  document.getElementById('byteType').value = jsoned_resp['size_calc'];
  handle_bytes_to_readable(jsoned_resp['max_torrentx_file_size']);
  });
}

function updateUnitOptions(unitType) {
  const select = document.getElementById('fileSizeByteType');
  let units;

  if (unitType === 'SI') {
    units = ['KB', 'MB'];
  } else {
    units = ['KiB', 'MiB'];
  }

  select.innerHTML = ''; // Clear existing options

  units.forEach((unit) => {
    const option = document.createElement('option');
    option.value = unit;
    option.textContent = unit;
    select.appendChild(option);
  });

}

function handle_bytes_to_readable (bytes, type){
  // that function always gets bytes, type and as a result will update
  // options type, readable size (value and mb\kb)
  updateUnitOptions(unitType);
  var values_arr = humanFileSize(bytes, type == "SI");
  document.getElementById('TorrentxSize').value = values_arr[0];
  document.getElementById('fileSizeByteType').value = values_arr[1];
  
}

function on_type_change(){
  // if now were
}