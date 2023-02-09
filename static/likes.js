    'use strict';
var imgs = document.querySelectorAll(".image");
var likes = document.querySelectorAll(".like-post-btn");

for (var i = 0; i < likes.length; i++) {
  (function(index) {
    likes[index].addEventListener('click', function() {
      if (imgs[index].src === "http://127.0.0.1:8000/static/hand-thumbs-up-fill.svg") {
        imgs[index].src = "http://127.0.0.1:8000/static/hand-thumbs-up.svg";
      }
      else{
        imgs[index].src = "http://127.0.0.1:8000/static/hand-thumbs-up-fill.svg";
      }
    });
  })(i);
}
