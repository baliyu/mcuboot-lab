#include <zephyr/kernel.h>

int main(void)
{
	unsigned int n = 0;

	while (1) {
		printk("mcuboot-lab: app v1.0.0 running from slot 0, tick %u\n", n++);
		k_sleep(K_SECONDS(1));
	}
	return 0;
}
