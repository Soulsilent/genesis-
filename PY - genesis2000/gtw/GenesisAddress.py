#!/usr/bin/env python3
# -*- coding:utf-8 -*-
address_val='''
JOB_9.00a2 => 0285E484 
STEP_9.00a2 => 0285E3BD 
JOB_1.03a2 => 0285E484 
STEP_1.03a2 => 0285E3BD 
JOB_9.01d1 => 02DA8B34 
STEP_9.01d1 => 02DA8A6D 
JOB_9.02b => 02F7E6D4 
STEP_9.02b => 02F7E60D 
JOB_2.02b => 02F7E6D4 
STEP_2.02b => 02F7E60D 
JOB_9.02c2 => 02FE6FE4 
STEP_9.02c2 => 02FE6F1D 
JOB_2.02c2 => 02FE6FE4 
STEP_2.02c2 => 02FE6F1D 
JOB_9.02c3 => 02D522B4 
STEP_9.02c3 => 02D521ED 
JOB_2.02c3 => 02D522B4 
STEP_2.02c3 => 02D521ED 
JOB_9.05a4 => 02EB1AB4 
STEP_9.05a4 => 02EB19ED 
JOB_2.05a4 => 02EB1AB4 
STEP_2.05a4 => 02EB19ED 
JOB_9.06b => 02EC0FA4 
STEP_9.06b => 02EC0EDD 
JOB_2.06b => 02EC0FA4 
STEP_2.06b => 02EC0EDD 
JOB_9.06b2 => 02EC1C94 
STEP_9.06b2 => 02EC1BCD 
JOB_2.06b2 => 02EC1C94 
STEP_2.06b2 => 02EC1BCD 
JOB_9.07b => 02FE2914 
STEP_9.07b => 02FE284D 
JOB_2.07b2 => 02FE2914 
STEP_2.07b2 => 02FE284D 
JOB_9.07b2 => 02FE623C 
STEP_9.07b2 => 02FE6175 
JOB_2.07b2 => 02FE623C 
STEP_2.07b2 => 02FE6175 
JOB_9.08a3 => 0307B76C 
STEP_9.08a3 => 0307B6A5 
JOB_2.08a3 => 0307B76C 
STEP_2.08a3 => 0307B6A5 
JOB_9.09a3 => 0307BF84 
STEP_9.09a3 => 0307BEBD 
JOB_2.09a3 => 0307BF84 
STEP_2.09a3 => 0307BEBD 
JOB_9.09b2 => 03100024 
STEP_9.09b2 => 030FFF5D 
JOB_2.09b2 => 03100024 
STEP_2.09b2 => 030FFF5D 
JOB_9.09b3 => 03100074 
STEP_9.09b3 => 030FFFAD 
JOB_2.09b3 => 03100074 
STEP_2.09b3 => 030FFFAD 
JOB_10.00 => 0313C384 
STEP_10.00 => 0313C2BD 
JOB_3.00 => 0313C384 
STEP_3.00 => 0313C2BD 
JOB_10.00a3 => 0315B444 
STEP_10.00a3 => 0315B37D 
JOB_3.00a3 => 0315B444 
STEP_3.00a3 => 0315B37D 
JOB_10.00b => 0315D784 
STEP_10.00b => 0315D6BD 
JOB_3.00b => 0315D784 
STEP_3.00b => 0315D6BD 
JOB_10.01b => 0325025C 
STEP_10.01b => 03250195 
JOB_3.01b => 0325025C 
STEP_3.01b => 03250195 
JOB_10.01b3 => 03252B34 
STEP_10.01b3 => 03252A6D 
JOB_3.01b3 => 03252B34 
STEP_3.01b3 => 03252A6D 
JOB_10.02 => 032665F4 
STEP_10.02 => 0326652D 
JOB_3.02 => 032665F4 
STEP_3.02 => 0326652D 
JOB_10.03bPR => 033039A4 
STEP_10.03bPR => 033038DD 
JOB_3.03bPR => 033039A4 
STEP_3.03bPR => 033038DD
STEP_10.05 => 03312555
JOB_10.05 => 0331261C
STEP_14.0 => 0333EE4D
JOB_14.0 => 0333EF14
'''

def get_address():
    address_list = list(filter(None,address_val.split('\n')))
    job_address = {}
    step_address = {}
    for i in address_list:
        v_key,v_val = i.split('=>')
        if 'JOB' in v_key:
            job_address[v_key.strip()] = v_val.strip()
        else:
            step_address[v_key.strip()] = v_val.strip()

    return job_address,step_address


if __name__ == '__main__':
    job_address,step_address = get_address()
    print(job_address)
    # print(step_address)



