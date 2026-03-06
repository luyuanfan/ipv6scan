FROM postgres:17

RUN apt -y update
RUN apt -y install python3 pip postgresql postgresql-plpython3-17
