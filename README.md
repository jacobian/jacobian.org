# The code that runs jacobian.org (soon)

New year, new site.

This is a fork of [Simon Willison's simonwillisonblog](https://github.com/simonw/simonwillisonblog), the code that runs his site. All the good parts come from him, all the jank comes from me.

## gcloud notes

database setup (because creating a db role through the gcloud cli/console creates a superuser):

get a sql shell (cloud shell -> `gcloud sql connect jacobian-apps`), then:

```sql
create database jacobiandotorg;
create role jacobiandotorg with login password '...';
grant all on database jacobiandotorg to jacobiandotorg;
```

