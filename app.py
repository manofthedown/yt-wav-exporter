from flask import Flask, request, jsonify, send_file
import subprocess
import os
import re
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_youtube_url(url):
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
    return bool(re.match(pattern, url))

def download_youtube_audio(url):
    try:
        # First download bestaudio (webm/m4a)
        temp_pattern = os.path.join(OUTPUT_DIR, 'temp_audio.%(ext)s')
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio',
            '-o', temp_pattern,
            '--no-playlist',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr
            if "Video unavailable" in error_msg:
                return None, "Video is unavailable or private"
            if "ERROR" in error_msg:
                match = re.search(r'ERROR:\s*(.+)', error_msg)
                if match:
                    return None, match.group(1).strip()
            return None, f"Failed to download: {result.stderr[:200]}"
        
        # Find the downloaded file
        temp_file = None
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith('temp_audio.'):
                temp_file = os.path.join(OUTPUT_DIR, f)
                break
        
        if not temp_file or not os.path.exists(temp_file):
            # Check stderr for what happened
            return None, f"Download failed: {result.stderr[:300]}"
        
        # Convert to wav using ffmpeg - output to unique name to avoid same-file conflict
        output_name = f"output_{uuid.uuid4().hex[:8]}.wav"
        wav_file = os.path.join(OUTPUT_DIR, output_name)
        convert_cmd = [
            'ffmpeg',
            '-y',
            '-i', temp_file,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            wav_file
        ]
        conv_result = subprocess.run(convert_cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if conv_result.returncode != 0:
            return None, f"Conversion failed: {conv_result.stderr}"
        
        if os.path.exists(wav_file):
            return wav_file, None
        
        return None, "No audio file generated"
    
    except FileNotFoundError:
        return None, "yt-dlp not installed. Run: pip install yt-dlp"
    except Exception as e:
        return None, str(e)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'Please enter a YouTube URL'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'success': False, 'error': 'Invalid YouTube URL'}), 400
    
    filepath, error = download_youtube_audio(url)
    
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    if filepath:
        filename = os.path.basename(filepath)
        return jsonify({'success': True, 'file': filename})
    
    return jsonify({'success': False, 'error': 'Unknown error'}), 500

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join(OUTPUT_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({'error': 'File not found'}), 404

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube to WAV</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: #0d0d0d;
            background: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #0d0d0d 70%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 40px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            animation: fadeIn 0.3s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header {
            text-align: center;
            margin-bottom: 32px;
        }
        .header h1 {
            color: #fff;
            font-size: 28px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        .header .icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #00f0ff, #8b5cf6);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .header .icon svg {
            width: 20px;
            height: 20px;
            fill: #fff;
        }
        .input-group {
            margin-bottom: 20px;
        }
        input[type="url"] {
            width: 100%;
            padding: 16px 20px;
            background: #252525;
            border: 2px solid #333;
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        input[type="url"]:focus {
            outline: none;
            border-color: #00f0ff;
        }
        input[type="url"]::placeholder {
            color: #666;
        }
        .btn {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #00f0ff;
            color: #0d0d0d;
        }
        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.4);
        }
        .btn-primary:disabled {
            background: #444;
            color: #888;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-secondary {
            background: #8b5cf6;
            color: #fff;
            margin-top: 16px;
        }
        .btn-secondary:hover {
            background: #9f6fff;
        }
        .status {
            margin-top: 20px;
            text-align: center;
            color: #888;
            font-size: 14px;
            min-height: 20px;
        }
        .status.error {
            color: #ff6b6b;
        }
        .status.success {
            color: #00f0ff;
        }
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #333;
            border-radius: 2px;
            margin-top: 20px;
            overflow: hidden;
            display: none;
        }
        .progress-bar.active {
            display: block;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00f0ff, #8b5cf6);
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s;
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>
                <div class="icon">
                    <svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
                </div>
                YouTube to WAV
            </h1>
        </div>
        <div class="input-group">
            <input type="url" id="urlInput" placeholder="Paste YouTube URL here..." autocomplete="off">
        </div>
        <button class="btn btn-primary" id="exportBtn">Export to WAV</button>
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="status" id="status"></div>
    </div>

    <script>
        const urlInput = document.getElementById('urlInput');
        const exportBtn = document.getElementById('exportBtn');
        const status = document.getElementById('status');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');

        let downloadLink = null;

        exportBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            if (!url) {
                status.textContent = 'Please enter a YouTube URL';
                status.className = 'status error';
                return;
            }

            status.textContent = 'Converting...';
            status.className = 'status';
            progressBar.classList.add('active');
            progressFill.style.width = '30%';
            exportBtn.disabled = true;
            exportBtn.textContent = 'Converting...';

            if (downloadLink) {
                downloadLink.remove();
                downloadLink = null;
            }

            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();
                progressFill.style.width = '70%';

                if (data.success) {
                    status.textContent = 'Conversion complete!';
                    status.className = 'status success';
                    progressFill.style.width = '100%';

                    downloadLink = document.createElement('a');
                    downloadLink.href = '/download/' + encodeURIComponent(data.file);
                    downloadLink.download = data.file;
                    downloadLink.className = 'btn btn-secondary';
                    downloadLink.textContent = 'Download WAV';
                    downloadLink.style.display = 'block';
                    downloadLink.style.textAlign = 'center';
                    downloadLink.style.textDecoration = 'none';
                    status.parentNode.insertBefore(downloadLink, status.nextSibling);

                    setTimeout(() => {
                        progressBar.classList.remove('active');
                    }, 1000);
                } else {
                    status.textContent = data.error || 'Conversion failed';
                    status.className = 'status error';
                    progressBar.classList.remove('active');
                }
            } catch (err) {
                status.textContent = 'Error: ' + err.message;
                status.className = 'status error';
                progressBar.classList.remove('active');
            }

            exportBtn.disabled = false;
            exportBtn.textContent = 'Export to WAV';
        });

        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') exportBtn.click();
        });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)