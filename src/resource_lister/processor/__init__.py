# Import all processor classes to make them available
from ._metric_processor import process as metric_process
from ._regional_paginate import process as regional_paginate_process
from ._regional_no_paginate import process as regional_no_paginate_process
from ._global_paginate import process as global_paginate_process
from ._global_no_paginate import process as global_no_paginate_process

# Make them available for import
__all__ = [
    'metric_process',
    'regional_paginate_process', 
    'regional_no_paginate_process',
    'global_paginate_process',
    'global_no_paginate_process'
]
