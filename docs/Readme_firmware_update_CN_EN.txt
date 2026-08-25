------------------------------------------------------------------------------
 固件适用机型及主板版本

 打印机型号：Ender-3 S1 
主板主控芯片型号： STM32F401
说明：
  该固件为Ender-3 S1 升级版本，支持中英双语，支持加装激光打印模块，更新后可切换FDM和激光打印。更新固件前请确认主控芯片型号，仅支持主控芯片是F401版本的机型。


固件更新内容：
    1.新增模型图片预览功能
    2.支持高速打印(160mm/s) & 振纹优化
    3.支持自动PID设置
    4.可展示/编辑调平数据
  
屏幕更新说明：
    1. 在电脑端格式化TF卡，分配单元大小选择4096。
    2. 将“dcboot.bin”放入TF卡中。
    3. 关闭打印机，将TF卡插入屏幕背面卡槽。
    4. 重启等待更新完成。
    5. 完成更新后取出TF卡，删除里面的“dcboot.bin”，将“private”、”TJC_SET“、“DWIN_SET”文件夹和firmware.zlib放入TF卡。
    6.关闭打印机，将TF卡插入屏幕背面卡槽。
    7. 重启等待更新完成。
    8.完成更新后取出TF卡，并删除里面的内容。
主板更新：
   1. 在电脑端格式化SD卡，分配单元大小选择4096。
   1. 将STM32F4_UPDATE文件夹放入SD卡(这一步骤是必须的，请注意）。
   3. 关闭打印机，将SD卡插入主板卡槽。
   4. 重启等待更新完成。
   5. 完成更新后取出SD卡，并删除里面的bin文件。
-------------------------------------------------------------------------------
Printer: Ender-3 S1 
Motherboard main control chip version: STM32F401
Notes: 
  The firmware is Ender-3 S1 update version, support Chinese and English bilingual, support adding laser printing module, after updating, you can switch between FDM and laser printing. Please confirm the main control chip model before updating the firmware, only support the model whose main control chip is F401 version.

Firmware update contents:
    1. New model picture preview function
    2. Support high-speed printing (160mm/s) & optimization of vibration pattern
    3. Support automatic PID setting
    4. Display/edit leveling data
  
Display firmware update：
   1. Format the TF card on the computer and select 4096 as the allocation unit size.
   2. Put "dcboot.bin" into the TF card. 
   3. Turn off the printer and insert the TF card into the card slot at the back of the screen. 
   4. Reboot and wait for the update to finish. 
   5. After the update, remove the TF card, delete the "dcboot.bin" and put the "private", "TJC_SET",    "DWIN_SET" and "DWIN_SET" folder and firmware.zlib into the TF card.
   6. Turn off the printer and insert the TF card into the card slot at the back of the screen. 
   7. Reboot and wait for the update to finish.
   8.After finishing the update, remove the TF card and delete the files inside.


Mainboard firmware update：
   1. Format the SD card on the computer side, and select 4096 for the allocation unit size.
   2. Put the STM32F4_UPDATE folder into the SD card  (THIS STEP IS REQUIRED， PLEASE NOTE！).
   3. Turn off the printer and insert the SD card into the card slot on the motherboard.  
   4. Reboot and wait for the update to finish.
   5. After finishing the update, remove the SD card from the motherboard slot and delete the bin file inside.

