from pymatgen.entries.compatibility import *

class MaterialsProjectCompatibility(Compatibility):
    """
    This class implements the GGA/GGA+U mixing scheme, which allows mixing of
    entries. Note that this should only be used for VASP calculations using the
    MaterialsProject parameters (see pymatgen.io.vaspio_set.MPVaspInputSet).
    Using this compatibility scheme on runs with different parameters is not
    valid.

    Args:
        compat_type: Two options, GGA or Advanced.  GGA means all GGA+U
            entries are excluded.  Advanced means mixing scheme is
            implemented to make entries compatible with each other,
            but entries which are supposed to be done in GGA+U will have the
            equivalent GGA entries excluded. For example, Fe oxides should
            have a U value under the Advanced scheme. A GGA Fe oxide run
            will therefore be excluded under the scheme.
        correct_peroxide: Specify whether peroxide/superoxide/ozonide
            corrections are to be applied or not.
        check_potcar_hash (bool): Use potcar hash to verify potcars are correct.
    """

    def __init__(self, compat_type="Advanced", correct_peroxide=True,
                 check_potcar_hash=False,check_potcar=False):
        self.compat_type = compat_type
        self.correct_peroxide = correct_peroxide
        self.check_potcar_hash = check_potcar_hash
        fp = os.path.join(MODULE_DIR, "MPCompatibility.yaml")
        if check_potcar:
            super(MaterialsProjectCompatibility, self).__init__(
               [PotcarCorrection(MPRelaxSet, check_hash=check_potcar_hash),
                GasCorrection(fp),
                AnionCorrection(fp, correct_peroxide=correct_peroxide),
                UCorrection(fp, MPRelaxSet, compat_type)])
        else:
            super(MaterialsProjectCompatibility, self).__init__(
               [GasCorrection(fp),
                AnionCorrection(fp, correct_peroxide=correct_peroxide),
                UCorrection(fp, MPRelaxSet, compat_type)])
