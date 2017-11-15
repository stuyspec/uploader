var hi = 3;

const request = require("request");
const fs = require("fs");
const axios = require("axios");
const FormData = require('form-data');

var form = new FormData();
/*
const filepath = 'tmp.png';

var data = {
  medium: {
    attachment: fs.createReadStream(filepath),
    title: "hi there"
  }
};
var myData = JSON.stringify({age: 12});

form.append('attachment', fs.createReadStream(filepath));
var url = "https://requestb.in/15hg2zo1";
url = 'http://localhost:3000/media';

axios.post(url, form);
// req = request.post(url, function (error, response, body) {
//   if (!error) {
//     //console.log(body);
//   }
// });*/

const data = {
  attachment: request('http://nodejs.org/images/logo.png')
};
form.append('attachment',request('http://nodejs.org/images/logo.png'));
//form.append('medium', JSON.stringify(data));

form.submit('http://localhost:3000/media', function(err, res) {
  // res – response object (http.IncomingMessage)  //
  res.resume();
});