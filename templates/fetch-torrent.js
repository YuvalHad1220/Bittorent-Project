function humanFileSize(bytes, si=false, dp=1) {
    const thresh = si ? 1000 : 1024;
  
    if (Math.abs(bytes) < thresh) {
      return bytes + ' B';
    }
  
    const units = si 
      ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'] 
      : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    let u = -1;
    const r = 10**dp;
  
    do {
      bytes /= thresh;
      ++u;
    } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
  
  
    return bytes.toFixed(dp) + ' ' + units[u];
  }


async function fetch_torrents(){
    // we will fetch all available torrents at the beginning. 
    var data = {
        'count': 50,
        'type': 'torrentx',
        'count_from_id': 0
    }

    var resp = await fetch('http://127.0.0.1:12345/torrents' ,
    {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
        body: JSON.stringify(data)

    })

    return resp.json()
}


function build_row(torrent_dict, table, index){
var row = table.insertRow(index);
var checkbox_input = document.createElement('input')
checkbox_input.type = 'checkbox'
row.insertCell(0).appendChild(checkbox_input)

// not keys of the dict, but kys that we need to add to row
var keys = ['index', 'name', 'state', '_type', 'protocol', 'size', 'progress', 'download_speed', 'downloaded', 'upload_speed', 'uploaded', 'seeders', 'leechers']
for (var i = 0; i<keys.length; i++){
    var current_cell = row.insertCell(i + 1);
    var node = document.createElement('p')
    var key = keys[i]

    switch(key){
        case 'name':
            node = document.createElement('a')
            node.text = torrent_dict['name']
            node.classList.add('has-text-weight-semibold')
            node.href = "#"
            break
        case 'size':
        case 'downloaded':
        case 'uploaded':
            node.innerText = humanFileSize(torrent_dict[key])
            break
        case 'progress':
            node = document.createElement('progress')
            node.text = "15%"
            node.value = 15
            node.max = 100
            node.classList.add("progress")
            break

        case 'download_speed':
        case 'upload_speed':
            node.innerText = humanFileSize(torrent_dict[key]) + "/s"
            break

        case 'leechers':
        case 'seeders':
            node.innerText = torrent_dict[key] + ' (' + torrent_dict['connected_' + key] + ')';
            break

        default:
            node.innerText = torrent_dict[key]

    }

    current_cell.appendChild(node)

}


}

function rebuild_table(){
    const table = document.getElementById("torrentlist")
    while(table.rows.length > 1) {
        table.deleteRow(-1);
      }
    fetch_torrents().then(torrent_list =>{
        torrent_list.forEach(torrent_dict => build_row(torrent_dict, table, -1))
    })
    
}
