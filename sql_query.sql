insert into oc_ce_hist (select * from oc_ce);
insert into oc_pe_hist (select * from oc_pe);
delete from oc_ce;
delete from oc_pe;