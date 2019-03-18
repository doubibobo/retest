libreoffice ��װ
��װ���壺https://blog.csdn.net/qq_30554229/article/details/80093894

https://blog.csdn.net/qq_41090453/article/details/83451321

<<<<<<< HEAD
    app.run(threaded=True, debug=False, host='0.0.0.0', port=80)


server {
    listen  80;
    server_name 95.179.160.135;
    location / {
        include         uwsgi_params;
        uwsgi_pass      127.0.0.1:8080;
        uwsgi_param     UWSGI_PYHOME /root/retest/venv;
        uwsgi_param     UWSGI_CHDIR  /root/retest;
        uwsgi_param     UWSGI_SCRIPT manage:app;
    }
    error_page 404 /404.html;
        location = /40x.html {
    }
    error_page 500 502 503 504 /50x.html;
        location = /50x.html {
    }
}