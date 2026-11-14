/* x17: submitted in the same session right after x16: is the session alive, and was the step after the ABORT run? */
%put X17 EXIST_BEFORE=%sysfunc(exist(work.x16_before)) EXIST_AFTER=%sysfunc(exist(work.x16_after));
