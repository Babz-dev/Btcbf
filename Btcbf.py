import requests
from bit import Key
from time import sleep, time
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from pybloom import BloomFilter
import hashlib

if not os.path.exists(os.getcwd() + "/cache.txt"):
    open("cache.txt", "w+")

def generate_sequential_keys(start=0):
    while True:
        yield Key().from_int(start)
        start += 1

class Btcbf():
    def __init__(self):
        self.start_t = 0
        self.prev_n = 0
        self.cur_n = 0
        self.start_n = 0
        self.end_n = 0
        self.seq = False
        self.privateKey = None
        self.start_r = 0
        
        # Load addresses and create a Bloom filter for faster lookup
        loaded_addresses = open("address.txt", "r").readlines()
        loaded_addresses = [x.rstrip() for x in loaded_addresses if 'wallet' not in x and len(x) > 0]
        self.bloom = BloomFilter(capacity=len(loaded_addresses), error_rate=0.001)
        for address in loaded_addresses:
            self.bloom.add(address)
        
        # Initialize generator for sequential brute forcing
        self.sequential_key_generator = generate_sequential_keys(self.start_n)
        
    def speed(self):
        while True:
            if self.cur_n != 0:
                cur_t = time()
                n = self.cur_n
                if self.prev_n == 0:
                    self.prev_n = n
                elapsed_t = cur_t - self.start_t
                print("current n: "+str(n)+", current rate: "+str(abs(n - self.prev_n) // 2) + "/s" +
                      f", elapsed time: [{str(elapsed_t // 3600)[:-2]}:{str(elapsed_t // 60 % 60)[:-2]}:{int(elapsed_t % 60)}], total: {n - self.start_r} ", end="\r")
                self.prev_n = n
                if self.seq:
                    open("cache.txt", "w").write(f"{self.cur_n}-{self.start_r}-{self.end_n}")
            sleep(2)
        
    def random_brute(self, n):
        self.cur_n = n
        key = Key()
        if key.address in self.bloom:  # Use Bloom filter for faster lookup
            print("Wow matching address found!!")
            print("Public Address: " + key.address)
            print("Private Key: " + key.to_wif())
            with open("foundkey.txt", "a") as f:
                f.write(key.address + "\n")
                f.write(key.to_wif() + "\n")
            sleep(510)
            exit()
            
    def sequential_brute(self, n):
        self.cur_n = n
        key = next(self.sequential_key_generator)  # Fetch the next key in sequence
        if key.address in self.bloom:  # Use Bloom filter for faster lookup
            print("Wow matching address found!!")
            print("Public Address: " + key.address)
            print("Private Key: " + key.to_wif())
            with open("foundkey.txt", "a") as f:
                f.write(key.address + "\n")
                f.write(key.to_wif() + "\n")
            sleep(500)
            exit()
    
    def random_online_brute(self, n):
        self.cur_n = n
        key = Key()
        the_page = requests.get("https://blockchain.info/q/getreceivedbyaddress/" + key.address + "/").text
        if int(the_page) > 0:
            print("Wow active address found!!")
            print("Public Address: " + key.address)
            print("Private Key: " + key.to_wif())
            with open("foundkey.txt", "a") as f:
                f.write(key.address + "\n")
                f.write(key.to_wif() + "\n")
            sleep(500)
            exit()
            
    def num_of_cores(self):
        available_cores = cpu_count()
        cores = input(f"\nNumber of available cores: {available_cores}\n \n How many cores to be used? (leave empty to use all available cores) \n \n Type something>")
        if cores == "":
            self.cores = int(available_cores)
        elif cores.isdigit():
            cores = int(cores)
            if 0 < cores <= available_cores:
                self.cores = cores
            elif cores <= 0:
                print(f"Hey you can't use {cores} number of CPU cores!!")
                input("Press Enter to exit")
                raise ValueError("negative number!")
            elif cores > available_cores:
                print(f"\n You only have {available_cores} cores")
                core_input = input(f"Are you sure you want to use {cores} cores? [y]es or [n]o>")
                self.cores = cores if core_input == "y" else available_cores
        else:
            print("Wrong input!")
            input("Press Enter to exit")
            exit()
            
    def generate_random_address(self):
        key = Key()
        print("\nPublic Address: " + key.address)
        print("Private Key: " + key.to_wif())
    
    def generate_address_from_key(self):
        if self.privateKey:
            key = Key(self.privateKey)
            print("\nPublic Address: " + key.address)
            print("\nYour wallet is ready!")
        else:
            print("No private key entered.")
    
    def get_user_input(self):
        user_input = input("\nWhat do you want to do? \n[1]: generate random key pair \n[2]: generate public address from private key \n[3]: brute force bitcoin offline mode \n[4]: brute force bitcoin online mode \n[0]: exit \n\n>")
        if user_input == "1":
            self.generate_random_address()
            print("\nYour wallet is ready!")
            input("\nPress Enter to exit")
            exit()
        elif user_input == "2":
            self.privateKey = input("\nEnter Private Key>")
            try:
                self.generate_address_from_key()
            except:
                print("\nIncorrect key format")
            input("Press Enter to exit")
            exit()
        elif user_input == "3":
            method_input = input("Enter the desired number: \n[1]: random attack \n[2]: sequential attack \n[0]: exit \n\n>")
            target = self.random_brute if method_input == "1" else self.sequential_brute
            if method_input in ("1", "2"):
                with ThreadPoolExecutor(max_workers=self.num_of_cores()) as pool:
                    self.start_t = time()
                    r = range(1000000) if method_input == "1" else range(self.start_n, self.end_n)
                    for i in r:
                        pool.submit(target, i)
                print("Stopping\n")
                exit()
        elif user_input == "4":
            print("Sequential online attack will be available soon!")
            input("Press Enter to exit")
            exit()
        elif user_input == "0":
            print("Exiting...")
            sleep(2)
            exit()
        else:
            print("No input. Generating random address.")
            self.generate_random_address()
            print("Your wallet is ready!")
            input("Press Enter to exit")
            exit()

if __name__ == "__main__":
    obj = Btcbf()
    try:
        t0 = threading.Thread(target=obj.get_user_input)
        t1 = threading.Thread(target=obj.speed)
        t1.daemon = True
        t0.daemon = True
        t0.start()
        t1.start()
        sleep(4000000)
    except KeyboardInterrupt:
        print("\n\nCtrl+C pressed. Exiting...")
        exit()
	
