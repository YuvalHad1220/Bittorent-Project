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
        load_settings_into_fields().then(() => openModal($target));
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
  
      if (e.keyCode === 27) { // Escape key
        closeAllModals();
      }
    });

  });

async function load_settings_into_fields(){
  var resp = await fetch('http://127.0.0.1:12345/edit_settings',
  {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  });

  resp = await resp.json()
  document.getElementById('defaultdownloadPath').value = resp['default_download_path'];
  document.getElementById('defaultArchivePath').value = resp['default_file_archive_path'];
  document.getElementById('TorrentxSize').value = resp['max_torrentx_file_size'];
  document.getElementById('port').value = resp['port'];
  document.getElementById('byteType').value = resp['size_calc'];
  parse_torrent_size()
  return resp;
}
function humanFileSize(bytes, si, dp=1) {
  const thresh = si ? 1000 : 1024;
  const units = si 
    ? ['KB'.toUpperCase(), 'MB'.toUpperCase()]
    : ['KiB', 'MiB'];
  let u = -1;
  const r = 10**dp;

  do {
    bytes /= thresh;
    ++u;
  } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);

  
  alert (bytes.toFixed(dp) + ' ' + units[u]);
  return [1,2]
}

function display_correct_torrent_size(){
  var old_type = null;
  if (document.getElementById('byteType').value == "IEC"){
    old_type = "SI";
    var options = document.getElementById('fileSizeByteType');
    options[0].value = "KiB";
    options[0].text = "KiB";
    options[1].value = "MiB";
    options[1].text = "MiB";
  }

  if (document.getElementById('byteType').value == "SI"){
    old_type = "IEC";
    var options = document.getElementById('fileSizeByteType');
    options[0].value = "KB";
    options[0].text = "KB";
    options[1].value = "MB";
    options[1].text = "MB";
    old_type = "IEC";
  }
  torrent_size_to_bytes(old_type);
  parse_torrent_size();
}
function torrent_size_to_bytes(old_type){
  var thresh = old_type == "SI" ? 1000 : 1024;
  var kbmbindex = document.getElementById('fileSizeByteType').selectedIndex;
  var oldval = document.getElementById('TorrentxSize').value;
  thresh = thresh ** (1+kbmbindex);
  document.getElementById('TorrentxSize').value = oldval * thresh;

}
function _torrent_size_to_bytes(){
  var thresh = document.getElementById('byteType').value == "SI" ? 1000 : 1024;
  var kbmbindex = document.getElementById('fileSizeByteType').selectedIndex;
  var oldval = document.getElementById('TorrentxSize').value;
  thresh = thresh ** (1+kbmbindex);
  return oldval * thresh;

}


function parse_torrent_size(){
    // now that we have the correct size type we also need to show the correct torrent file size
    torrentx_max_size = parseInt(document.getElementById('TorrentxSize').value);
    var bool = document.getElementById('byteType').value == "SI";
    // if (bool){
    //     var options = document.getElementById('fileSizeByteType');
    //     options[0].value = "KB";
    //     options[0].text = "KB";
    //     options[1].value = "MB";
    //     options[1].text = "MB";
    //   }
    //   else {
    //     var options = document.getElementById('fileSizeByteType');
    //     options[0].value = "KiB";
    //     options[0].text = "KiB";
    //     options[1].value = "MiB";
    //     options[1].text = "MiB";
      
    // }
    torrent_size_arr = humanFileSize(torrentx_max_size, bool).split(' ');
    alert(torrent_size_arr);
    document.getElementById('fileSizeByteType').value = torrent_size_arr[1];
    document.getElementById('TorrentxSize').value = torrent_size_arr[0];
}


function update_settings(){
  var dict = {
    'default_download_path': document.getElementById('defaultdownloadPath').value,
    'default_file_archive_path': document.getElementById('defaultArchivePath').value,
    'port': document.getElementById('port').value,
    'size_calc': document.getElementById('byteType').value,
    'max_torrentx_file_size': _torrent_size_to_bytes()
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

    // .then(response => response.json())
    // .then(data => {
    //   alert(data)

}