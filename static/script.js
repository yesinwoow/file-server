function play(name){
  let player = document.getElementById('player');
  let video = document.getElementById('mainVideo');
  let source = document.getElementById('videoSource');

  source.src = '/video/' + name;
  video.load();

  player.style.display = 'flex';
}

document.getElementById('player').onclick = function(e){
  if(e.target.id === 'player'){
    this.style.display = 'none';
    document.getElementById('mainVideo').pause();
  }
}