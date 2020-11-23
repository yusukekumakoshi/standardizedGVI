# Standardized GVI
Calculate standardized GVI from GVI point data / original road network data / boundary data. The process uses [geovoronoi](https://github.com/WZBSocialScienceCenter/geovoronoi) package in order to achieve less-biased estimation of GVI at zonal level.

## Prepare a virtual environment
First, create a virtual environment and activate it.
```terminal
python3 -m venv ~/.sGVI
source ~/.sGVI/bin/activate
```

Due to dependency of rtree, install `spatialindex` via homebrew.
```terminal 
brew install spatialindex
```

Once spatialindex is installed, install all the other libraries, using `requirements.txt`.
```terminal 
# clone sGVI repository and install remaining dependencies using pip
git clone https://github.com/yusukekumakoshi/standardizedGVI.git
cd standardizedGVI
pip3 install -r requirements.txt
```

## Work flow
Input files are the followings:
* GVI point data
* Original road network data
* Boundary data

Original road network data must be the same network as that you used to calculate GVI in [Treepedia](https://github.com/y26805/Treepedia_Public).

Boundary data must be shapefile of polygons (any form is accepted).

Set the paths to those files in `sGVI.py`, run the following:

```terminal
python3 code/sGVI.py
```

## Reference
Kumakoshi, Y., Chan, S. Y., Koizumi, H., Li, X., & Yoshimura, Y. (2020). Standardized Green View Index and Quantification of Different Metrics of Urban Green Vegetation. _Sustainability, 12_(18), 7434.