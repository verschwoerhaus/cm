c3voc - configuration management
================================

** VSH EDITS **

# Installation

To manage hosts with [ansible](http://ansible.com/)  you only need to install `ansible` on your machine.

``` debian
  sudo aptitude install ansible
```


```
  pip2.7 install libkeepass pykeepass

```

# Usage

Syntax validation.

```
  ansible-playbook -i vsh -l mixers site.yml --syntax-check
```

Basic `ansible` call to deploy new config to a specific host.

```
  ansible-playbook --ask-pass --ask-become-pass -u voc --become --become-method=su -i vsh -l 10.73.1.3 site.yml
```

Basic `ansible` call to deploy new config to a set of hosts on an event.

```
  ./ansible-playbook-keepass -u voc --become --become-method=sudo -i vsh -l saal-vsh site.yml
```

# TODO

Have a look into `TODO` file.

# Docs

* `ansible-doc -l` lists all available modules
* `ansible-doc $module` opens a very helpful knowledge page for a given module
* [Documentation Page](http://docs.ansible.com/)
