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
  document.getElementById('randomPeerId').value = jsoned_resp['random_id'];
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
  // when we change type - bcz that field is not empty it thinks that whatever inside is new bytes. not good we need to fix asap
  // if (inputed_bytes_as_str !== ""){
  //   update_bytes(inputed_bytes_as_str);

  // }
  display_bytes();
}

function update_bytes(new_bytes){
  var value_in_humanreadable = parseFloat(new_bytes);
  var bytes = 0;
  var selected_value = document.getElementById("fileSizeByteType").value;

  // we want to get the value from the previous type, so we stich
  switch (selected_value) {
    case "KB":
      bytes = value_in_humanreadable * Math.pow(10,3);
      break;
    case "MB":
      bytes = value_in_humanreadable * Math.pow(10,6);

        break;
    case "KiB":
      bytes = value_in_humanreadable * Math.pow(2,10);

        break;
    case "MiB":
      bytes = value_in_humanreadable * Math.pow(2,20);


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
  document.getElementById('TorrentxSize').value = res_arr[0];
  document.getElementById('fileSizeByteType').value = res_arr[1];

}

function update_settings(){
  const select = document.getElementById("spoofingVersion");
  const selectedOption = select.options[select.selectedIndex];
  const value = selectedOption.value;
  const text = selectedOption.text;
  var dict = {
    'default_download_path': document.getElementById('defaultdownloadPath').value,
    'default_file_archive_path': document.getElementById('defaultArchivePath').value,
    'port': document.getElementById('port').value,
    'size_calc': document.getElementById('byteType').value,
    'max_torrentx_file_size': size_in_bytes,
    'user_agent': value,
    'peer_id': text,
    'random_id': document.getElementById("randomPeerId").value
  };
  console.log(JSON.stringify(dict))
  resp = fetch('http://127.0.0.1:12345/edit_settings',
  
  {
    'method': 'POST',
    body: JSON.stringify(dict),
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
});

}
function generateRandomId() {
  const characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  let randomId = '';
  for (let i = 0; i < 12; i++) {
    randomId += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  document.getElementById("randomPeerId").value = randomId;
}


async function fetchOptions() {
  // URL of the API that returns the list of options
  const apiUrl = "http://127.0.0.1:12345/get_available_clients";

  // Fetch the list of options from the API
  fetch(apiUrl, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  }).then(data => data.json())
  .then(jsoned_list => {
      // Get the select element
      var select = document.getElementById("spoofingVersion");

      // Clear the existing options
      select.innerHTML = "";

      // Add the new options to the select element
      jsoned_list.forEach(option => {
        var optionElement = document.createElement("option");
        optionElement.value = option[0];
        optionElement.text = option[1];
        select.add(optionElement);
      })
    });

}