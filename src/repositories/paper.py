from sqlalchemy.orm import Session


class PaperRepository:
    def __init__(self, session: Session):
        self.session = session

    