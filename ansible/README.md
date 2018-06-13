c3voc - configuration management
================================

** VSH EDITS **

# Installation

To manage hosts with [ansible](http://ansible.com/)  you only need to install `ansible` on your machine.

``` debian
  sudo aptitude install ansible
```

# Usage

Syntax validation.

```
  ansible-playbook -i event -l mixers site.yml --syntax-check
```

Basic `ansible` call to deploy new config to a specific host. Passwords will be pulled from keepass.

```
  ansible-playbook --ask-pass --ask-become-pass -u voc --become --become-method=su -i event -l 192.168.9.35 site.yml
```

Basic `ansible` call to deploy new config to a set of hosts on an event.

```
  ansible-playbook -u voc --become --become-method=sudo -i event -l salon site.yml
```

# TODO

Have a look into `TODO` file.

# Docs

* `ansible-doc -l` lists all available modules
* `ansible-doc $module` opens a very helpful knowledge page for a given module
* [Documentation Page](http://docs.ansible.com/)

---
# test decklink
voc@vocknoedel:~$ sudo ffmpeg -y -nostdin -f decklink -video_input hdmi -format_code '24ps' -i 1 -c:v rawvideo -c:a pcm_s16le -pix_fmt bgra -f fbdev /dev/fb0

# test zidoo:
ffmpeg -y -nostdin -xerror -f flv -i "rtmp://127.0.0.1/push/hdmi" -filter_complex "[0:v] scale=1920:1080,fps=25 [v]" -map "[v]" -c:v rawvideo -pix_fmt bgra -f fbdev /dev/fb0