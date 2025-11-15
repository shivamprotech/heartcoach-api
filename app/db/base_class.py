from sqlalchemy.orm import declarative_base
from sqlalchemy_continuum import make_versioned

make_versioned()
Base = declarative_base()
