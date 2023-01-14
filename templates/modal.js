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


let unitType = null;
let size_in_bytes = 0;

async function fetch_from_server(){
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
  unitType = jsoned_resp['size_calc'];
  document.getElementById('byteType').value = unitType; 
  size_in_bytes = jsoned_resp['max_torrentx_file_size'];
  update_type();
  });
}
function updateUnitOptions() {
  const select = document.getElementById('fileSizeByteType');
  let units;
  if (unitType === 'SI') {
    units = ['KB', 'MB'];
  } 
  else {
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
function update_type(){
  unitType = document.getElementById('byteType').value;
  // if user changes type, than maybe he also changed value so update size_in_bytes
  updateUnitOptions();
  var inputed_bytes_as_str = document.getElementById("TorrentxSize").value;
  if (inputed_bytes_as_str !== ""){
    update_bytes(inputed_bytes_as_str);

  }
  display_bytes();
}

function update_bytes(new_bytes){
  var value_in_humanreadable = parseFloat(new_bytes);
  var bytes = 0;
  var selected_value = document.getElementById("fileSizeByteType").value;

  // we want to get the value from the previous type, so we stich
  switch (selected_value) {
    case "KB":
      bytes = value_in_humanreadable * Math.pow(2,20);
      break;
    case "MB":
      bytes = value_in_humanreadable * Math.pow(2,30);

        break;
    case "KiB":
      bytes = value_in_humanreadable * Math.pow(10,6);

        break;
    case "MiB":
      bytes = value_in_humanreadable * Math.pow(10,12);

        break;
  }
  size_in_bytes = bytes;
}

// we need to change it! There are two functions loaded into this page. how do we care take care of it?
function humanFileSizeLocal(bytes) {
  const thresh = unitType == "SI" ? 1000 : 1024;
  const units = unitType == "SI" ? ['KB', 'MB']: ['KiB', 'MiB'];
  let u = -1;
  do {
    bytes /= thresh;
    ++u;
  } while (bytes >= thresh && u < units.length - 1);
  return [Math.round(bytes * 10) / 10, units[u]];
}

function display_bytes(){
  var res_arr = humanFileSizeLocal(size_in_bytes);
  alert(res_arr);
  document.getElementById('TorrentxSize').value = res_arr[0];
  document.getElementById('fileSizeByteType').value = res_arr[1];

}

