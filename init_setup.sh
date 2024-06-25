echo [$(date)]: "START"
echo [$(date)]: "Creating conda env with python 3.11" # CHANGE THE VERSION BASE DON YOUR WORK
conda create --prefix ./venv python=3.11 -y
echo [$(date)]: "activate virtual env"
source activate ./venv
echo [$(date)]: "intalling dev requirements with latest version"
pip install -r requirements_dev.txt --upgrade
# echo [$(date)]: "intalling dev requirements"
# pip install -r requirements_dev.txt
echo [$(date)]: "END"