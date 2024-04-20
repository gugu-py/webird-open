function copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
        // 支持新的 API
        navigator.clipboard.writeText(text)
          .then(function() {
            alert('已成功复制到剪贴板：' + text);
          })
          .catch(function(error) {
            alert('复制到剪贴板失败：' + error);
          });
        } else {
            // 兼容旧的浏览器
            var tempInput = document.createElement('input');
            tempInput.value = text;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            alert('已成功复制到剪贴板：' + text);
        }
    }