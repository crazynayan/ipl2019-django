# Fantasy League
This source code is to play an online fantasy league for a closed group of friends.

It is developed using Django framework and hosted on google app engine. 

# Deployment
## Cloud SQL
Turn on Cloud SQL in gcloud console.
```
cloud_sql_proxy.exe -instances="super-ipl-league-2019:asia-south1:ipl"=tcp:3306
mysqlsh
\c nayan@localhost:3306
\sql
show databases;
use ipl
show tables;
describe ipl2019_member;
select * from ipl2019_member;
\quit
```
## Application Deployment
```
gcloud config set project super-ipl-league-2019
gcloud info
gcloud app describe
gcloud app deploy
```