# django-optimization-helpers

## Intallation

### Getting the code

1a. ```pip install e- git+https://github.com/tomek-livenup/django-optimization-helpers/@master#egg=django-optimization-helpers```
2b. add ```pip install e- git+https://github.com/tomek-livenup/django-optimization-helpers/@master#egg=django-optimization-helpers``` to you requirement.txt and run ```pip install -r requirements.txt```


### Prerequisites
Add 'optimization_helpers' to your INSTALLED_APPS setting:

```
INSTALLED_APPS = [
    # ...
    'django.contrib.staticfiles',
    # ...
    'optimization_helpers',
]
```


## Usage

TODO


## TODO list

- [x] discover @property
- [ ] check multiple ForNode with the same var on level 0 (I think, we can provide filter "|something")
- [ ] working with endless pagination plugin
- [ ] better way to initilize (without need to set template name i.e.)
- [ ] "Usage" part of this documentation
- [ ] Short description of djang-optimization-helpers
- [ ] check/see what select_related/prefetch is already there and what we add
- [ ] showing results from dashboard.json on demand in template
- [ ] add some related to plugin settings

