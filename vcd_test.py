import sys
from vcd import VCDWriter

for layer_id in range(1):
    start_clk=-1
    finish_clk=0;
    task_cnt=0;
    #vcdfile = open('gemm_5layers/gemm_layer'+str(layer_id)+'.vcd','w')
    #vcdfile = open('layernorm/layernorm.vcd','w')
    vcdfile = open('XuLei_conv3x3/XuLei_conv3x3_'+str(layer_id)+'.vcd','w')
    #vcdfile = open('XuLei_conv1x1/nobias_'+str(layer_id)+'.vcd','w')
    #vcdfile = open('ddr_test2/ddr_test.vcd','w')
    with VCDWriter(vcdfile, timescale='1 ns', date='today') as writer:
        signal_table={}
        time_record={}
        time_sum={}
        prefetch_cnt={}
        compute_cnt={}
        write_back_cnt={}
        config_time=0
        running_prefetch_cnt=0
        config_start_time=0;
        
        prefetch_state={}
        write_back_state={}
        last_ddr_event={}
        ddr_time={}
        for i in range(16):
            time_record[i]={}
            signal_table[i]={}
            time_sum[i]={}
            prefetch_cnt[i]=0
            compute_cnt[i]=0
            write_back_cnt[i]=0
            prefetch_state[i]=0
            write_back_state[i]=0
            last_ddr_event[i]=0
            ddr_time[i]=0
            time_record[i]["prefetch_time"]={}
            time_record[i]["compute_time"]={}
            time_record[i]["write_back_time"]={}
            time_sum[i]["prefetch_time"]=0
            time_sum[i]["compute_time"]=0
            time_sum[i]["write_back_time"]=0
            slice="top.slice"+str(i)
            prefetch=writer.register_var(slice,"prefetch",'integer',size=1,init=0)
            signal_table[i]["prefetch"]=prefetch
            prefetch_time=writer.register_var(slice,"prefetch_time",'integer',size=32,init=0)
            signal_table[i]["prefetch_time"]=prefetch_time
            config=writer.register_var(slice,"config",'integer',size=1,init=0)
            signal_table[i]["config"]=config
            compute=writer.register_var(slice,"compute",'integer',size=1,init=0)
            signal_table[i]["compute"]=compute
            compute_time=writer.register_var(slice,"compute_time",'integer',size=32,init=0)
            signal_table[i]["compute_time"]=compute_time
            write_back=writer.register_var(slice,"write_back",'integer',size=1,init=0)
            signal_table[i]["write_back"]=write_back
            write_back_time=writer.register_var(slice,"write_back_time",'integer',size=32,init=0)
            signal_table[i]["write_back_time"]=write_back_time
            TG_id=writer.register_var(slice,"TG_id",'integer',size=10,init=0)
            signal_table[i]["TG_id"]=TG_id
        #with open('layernorm'+"/runtime_layernorm.log", "r") as f:
        #with open('gemm_5layers'+"/runtime_layer"+str(layer_id)+".log", "r") as f:
        #with open('ddr_test/'+"runtime.log", "r") as f:
        with open('XuLei_conv3x3'+"/XuLei_conv_conv3x3_"+str(layer_id)+"/runtime.log", "r") as f:
        #with open('XuLei_conv1x1'+"/nobias_"+str(layer_id)+"/runtime.log", "r") as f:
        #with open('ddr_test2'+"/runtime.log", "r") as f:
            # Read the contents of the file
            string = f.read()

        # Split the string into lines
        lines = string.split("\n")

        # Create an empty dictionary to store the information
        info = {}
        cycles = {}
        for line in lines:
            
            if "prefetch" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                clk_value = int(tokens[4])
                if "start" in line:
                    time_record[slice_num]["prefetch_time"][prefetch_cnt[slice_num]]=clk_value;
                    
                elif "finish" in line:
                    time_record[slice_num]["prefetch_time"][prefetch_cnt[slice_num]]=clk_value-time_record[slice_num]["prefetch_time"][prefetch_cnt[slice_num]];
                    time_sum[slice_num]["prefetch_time"]+=time_record[slice_num]["prefetch_time"][prefetch_cnt[slice_num]]
                    prefetch_cnt[slice_num]+=1
                    
            elif "run" in line or "access" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                clk_value = int(tokens[4])
                if "start" in line:
                    time_record[slice_num]["compute_time"][compute_cnt[slice_num]]=clk_value;
                elif "done" in line:
                    time_record[slice_num]["compute_time"][compute_cnt[slice_num]]=clk_value-time_record[slice_num]["compute_time"][compute_cnt[slice_num]];
                    time_sum[slice_num]["compute_time"]+=time_record[slice_num]["compute_time"][compute_cnt[slice_num]]
                    compute_cnt[slice_num]+=1
                    
            elif "write" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                clk_value = int(tokens[4])
                if "start" in line:
                    time_record[slice_num]["write_back_time"][write_back_cnt[slice_num]]=clk_value;
                elif "finish" in line:
                    time_record[slice_num]["write_back_time"][write_back_cnt[slice_num]]=clk_value-time_record[slice_num]["write_back_time"][write_back_cnt[slice_num]];
                    time_sum[slice_num]["write_back_time"]+=time_record[slice_num]["write_back_time"][write_back_cnt[slice_num]]
                    write_back_cnt[slice_num]+=1
                    
        for i in range(len(prefetch_cnt)):
            prefetch_cnt[i]=0
            compute_cnt[i]=0
            write_back_cnt[i]=0
        # Loop through each line and extract the relevant information
        
        for line in lines:
            if "prefetch" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                
                
                clk_value = int(tokens[4])
                if(start_clk==-1):
                    start_clk=clk_value;
                if "start" in line:
                    writer.change(signal_table[slice_num]["prefetch"],clk_value-start_clk,1)
                    writer.change(signal_table[slice_num]["prefetch_time"],clk_value-start_clk,time_record[slice_num]["prefetch_time"][prefetch_cnt[slice_num]])
                    if(running_prefetch_cnt==0):
                        config_time+=clk_value-start_clk-config_start_time
                    running_prefetch_cnt+=1   
                    
                    if(write_back_state[slice_num]==1):
                        ddr_time[slice_num]+= clk_value-start_clk-last_ddr_event[slice_num]
                    prefetch_state[slice_num]=1
                    last_ddr_event[slice_num]=clk_value-start_clk  
                elif "finish" in line:
                    writer.change(signal_table[slice_num]["prefetch"],clk_value-start_clk,0)
                    writer.change(signal_table[slice_num]["prefetch_time"],clk_value-start_clk,0)
                    running_prefetch_cnt-=1
                    prefetch_cnt[slice_num]+=1
                    
                    if(running_prefetch_cnt==0):
                        config_start_time=clk_value-start_clk;
                    ddr_time[slice_num]+= clk_value-start_clk-last_ddr_event[slice_num]
                    prefetch_state[slice_num]=0
                    last_ddr_event[slice_num]=clk_value-start_clk    
            elif "run" in line or "access" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                clk_value = int(tokens[4])
                if "start" in line:
                    writer.change(signal_table[slice_num]["compute"],clk_value-start_clk,1)
                    writer.change(signal_table[slice_num]["compute_time"],clk_value-start_clk,time_record[slice_num]["compute_time"][compute_cnt[slice_num]])
                elif "done" in line:
                    writer.change(signal_table[slice_num]["compute"],clk_value-start_clk,0)
                    writer.change(signal_table[slice_num]["compute_time"],clk_value-start_clk,0)
                    compute_cnt[slice_num]+=1
            elif "write" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                clk_value = int(tokens[4])
                if "start" in line:
                    writer.change(signal_table[slice_num]["write_back"],clk_value-start_clk,1)
                    writer.change(signal_table[slice_num]["write_back_time"],clk_value-start_clk,time_record[slice_num]["write_back_time"][write_back_cnt[slice_num]])
                    if(prefetch_state[slice_num]==1):
                        ddr_time[slice_num]+= clk_value-start_clk-last_ddr_event[slice_num]
                    write_back_state[slice_num]=1
                    last_ddr_event[slice_num]=clk_value-start_clk
                elif "finish" in line:
                    writer.change(signal_table[slice_num]["write_back"],clk_value-start_clk,0)
                    writer.change(signal_table[slice_num]["write_back_time"],clk_value-start_clk,0)
                    write_back_cnt[slice_num]+=1
                    ddr_time[slice_num]+= clk_value-start_clk-last_ddr_event[slice_num]
                    write_back_state[slice_num]=0
                    last_ddr_event[slice_num]=clk_value-start_clk
            elif "task" in line:
                tokens = line.split()
                slice_num = int(tokens[0][5:])
                event_type = tokens[1]
                clk_value = int(tokens[4])
                if "finish" in line:
                    task_cnt+=1
                    finish_clk=clk_value-start_clk
                    writer.change(signal_table[slice_num]["TG_id"],clk_value-start_clk,signal_table[slice_num]["TG_id"].value+1)
        print("****************************"+"layer_id"+str(layer_id)+"***************************")
        avg_prefetch_time=0;
        avg_compute_time=0
        avg_write_back_time=0
        avg_ddr_time=0
        for i in range(16):
            # print( "slice "+str(i)+" :")
            # print("prefetch_time: " ,time_sum[i]["prefetch_time"])
            # print("compute_time: " ,time_sum[i]["compute_time"])
            # print("write_back_time: " ,time_sum[i]["write_back_time"])
            # print("ddr_time: " ,time_sum[i]["write_back_time"]+time_sum[i]["prefetch_time"])
            avg_prefetch_time+=time_sum[i]["prefetch_time"]
            avg_compute_time+=time_sum[i]["compute_time"]
            avg_write_back_time+=time_sum[i]["write_back_time"]
            avg_ddr_time+=ddr_time[i]
        print("平均预取时间：",avg_prefetch_time/16)
        print("平均计算时间：",avg_compute_time/16)
        print("平均单task计算时间",avg_compute_time/task_cnt)
        print("平均写回时间：",avg_write_back_time/16)
        print("平均访存时间：",avg_ddr_time/16)
        print("配置时间：",config_time)
        print("总运行时间：",finish_clk)