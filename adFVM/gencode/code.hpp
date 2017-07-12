#ifndef CODE_H
#define CODE_H
#include "common.hpp"
#include "interface.hpp"
#include "density.hpp"

void Function_primitive(int n, const scalar* Tensor_15, const scalar* Tensor_13, const scalar* Tensor_14, scalar* Tensor_16, scalar* Tensor_26, scalar* Tensor_24);
void Function_primitive_grad(int n, const scalar* Tensor_15, const scalar* Tensor_13, const scalar* Tensor_14, const scalar* Tensor_27, const scalar* Tensor_28, const scalar* Tensor_29, scalar* Tensor_30, scalar* Tensor_31, scalar* Tensor_32);
void Function_conservative(int n, const scalar* Tensor_33, const scalar* Tensor_34, const scalar* Tensor_35, scalar* Tensor_40, scalar* Tensor_46, scalar* Tensor_45);
void Function_conservative_grad(int n, const scalar* Tensor_33, const scalar* Tensor_34, const scalar* Tensor_35, const scalar* Tensor_47, const scalar* Tensor_48, const scalar* Tensor_49, scalar* Tensor_50, scalar* Tensor_51, scalar* Tensor_52);
void Function_grad(int n, const scalar* Tensor_53, const scalar* Tensor_54, const scalar* Tensor_55, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_86, scalar* Tensor_93, scalar* Tensor_100);
void Function_grad_grad(int n, const scalar* Tensor_53, const scalar* Tensor_54, const scalar* Tensor_55, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_101, const scalar* Tensor_102, const scalar* Tensor_103, scalar* Tensor_104, scalar* Tensor_105, scalar* Tensor_106, scalar* Tensor_107, scalar* Tensor_108, scalar* Tensor_109, scalar* Tensor_110, scalar* Tensor_111, scalar* Tensor_112, scalar* Tensor_113, scalar* Tensor_114, integer* Tensor_115, integer* Tensor_116);
void Function_coupledGrad(int n, const scalar* Tensor_117, const scalar* Tensor_118, const scalar* Tensor_119, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_147, scalar* Tensor_151, scalar* Tensor_155);
void Function_coupledGrad_grad(int n, const scalar* Tensor_117, const scalar* Tensor_118, const scalar* Tensor_119, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_156, const scalar* Tensor_157, const scalar* Tensor_158, scalar* Tensor_159, scalar* Tensor_160, scalar* Tensor_161, scalar* Tensor_162, scalar* Tensor_163, scalar* Tensor_164, scalar* Tensor_165, scalar* Tensor_166, scalar* Tensor_167, scalar* Tensor_168, scalar* Tensor_169, integer* Tensor_170, integer* Tensor_171);
void Function_boundaryGrad(int n, const scalar* Tensor_172, const scalar* Tensor_173, const scalar* Tensor_174, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_181, scalar* Tensor_185, scalar* Tensor_189);
void Function_boundaryGrad_grad(int n, const scalar* Tensor_172, const scalar* Tensor_173, const scalar* Tensor_174, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_190, const scalar* Tensor_191, const scalar* Tensor_192, scalar* Tensor_193, scalar* Tensor_194, scalar* Tensor_195, scalar* Tensor_196, scalar* Tensor_197, scalar* Tensor_198, scalar* Tensor_199, scalar* Tensor_200, scalar* Tensor_201, scalar* Tensor_202, scalar* Tensor_203, integer* Tensor_204, integer* Tensor_205);
void Function_flux(int n, const scalar* Tensor_206, const scalar* Tensor_207, const scalar* Tensor_208, const scalar* Tensor_209, const scalar* Tensor_210, const scalar* Tensor_211, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_530, scalar* Tensor_536, scalar* Tensor_542, scalar* Tensor_555);
void Function_flux_grad(int n, const scalar* Tensor_206, const scalar* Tensor_207, const scalar* Tensor_208, const scalar* Tensor_209, const scalar* Tensor_210, const scalar* Tensor_211, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_556, const scalar* Tensor_557, const scalar* Tensor_558, const scalar* Tensor_559, scalar* Tensor_560, scalar* Tensor_561, scalar* Tensor_562, scalar* Tensor_563, scalar* Tensor_564, scalar* Tensor_565, scalar* Tensor_566, scalar* Tensor_567, scalar* Tensor_568, scalar* Tensor_569, scalar* Tensor_570, scalar* Tensor_571, scalar* Tensor_572, scalar* Tensor_573, integer* Tensor_574, integer* Tensor_575);
void Function_characteristicFlux(int n, const scalar* Tensor_576, const scalar* Tensor_577, const scalar* Tensor_578, const scalar* Tensor_579, const scalar* Tensor_580, const scalar* Tensor_581, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_852, scalar* Tensor_855, scalar* Tensor_858, scalar* Tensor_869);
void Function_characteristicFlux_grad(int n, const scalar* Tensor_576, const scalar* Tensor_577, const scalar* Tensor_578, const scalar* Tensor_579, const scalar* Tensor_580, const scalar* Tensor_581, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_870, const scalar* Tensor_871, const scalar* Tensor_872, const scalar* Tensor_873, scalar* Tensor_874, scalar* Tensor_875, scalar* Tensor_876, scalar* Tensor_877, scalar* Tensor_878, scalar* Tensor_879, scalar* Tensor_880, scalar* Tensor_881, scalar* Tensor_882, scalar* Tensor_883, scalar* Tensor_884, scalar* Tensor_885, scalar* Tensor_886, scalar* Tensor_887, integer* Tensor_888, integer* Tensor_889);
void Function_coupledFlux(int n, const scalar* Tensor_890, const scalar* Tensor_891, const scalar* Tensor_892, const scalar* Tensor_893, const scalar* Tensor_894, const scalar* Tensor_895, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_1211, scalar* Tensor_1214, scalar* Tensor_1217, scalar* Tensor_1228);
void Function_coupledFlux_grad(int n, const scalar* Tensor_890, const scalar* Tensor_891, const scalar* Tensor_892, const scalar* Tensor_893, const scalar* Tensor_894, const scalar* Tensor_895, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_1229, const scalar* Tensor_1230, const scalar* Tensor_1231, const scalar* Tensor_1232, scalar* Tensor_1233, scalar* Tensor_1234, scalar* Tensor_1235, scalar* Tensor_1236, scalar* Tensor_1237, scalar* Tensor_1238, scalar* Tensor_1239, scalar* Tensor_1240, scalar* Tensor_1241, scalar* Tensor_1242, scalar* Tensor_1243, scalar* Tensor_1244, scalar* Tensor_1245, scalar* Tensor_1246, integer* Tensor_1247, integer* Tensor_1248);
void Function_boundaryFlux(int n, const scalar* Tensor_1249, const scalar* Tensor_1250, const scalar* Tensor_1251, const scalar* Tensor_1252, const scalar* Tensor_1253, const scalar* Tensor_1254, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, scalar* Tensor_1303, scalar* Tensor_1306, scalar* Tensor_1309, scalar* Tensor_1320);
void Function_boundaryFlux_grad(int n, const scalar* Tensor_1249, const scalar* Tensor_1250, const scalar* Tensor_1251, const scalar* Tensor_1252, const scalar* Tensor_1253, const scalar* Tensor_1254, const scalar* Tensor_0, const scalar* Tensor_1, const scalar* Tensor_2, const scalar* Tensor_3, const scalar* Tensor_4, const scalar* Tensor_5, const scalar* Tensor_6, const scalar* Tensor_7, const integer* Tensor_8, const integer* Tensor_9, const scalar* Tensor_1321, const scalar* Tensor_1322, const scalar* Tensor_1323, const scalar* Tensor_1324, scalar* Tensor_1325, scalar* Tensor_1326, scalar* Tensor_1327, scalar* Tensor_1328, scalar* Tensor_1329, scalar* Tensor_1330, scalar* Tensor_1331, scalar* Tensor_1332, scalar* Tensor_1333, scalar* Tensor_1334, scalar* Tensor_1335, scalar* Tensor_1336, scalar* Tensor_1337, scalar* Tensor_1338, integer* Tensor_1339, integer* Tensor_1340);
void Function_CBC_TOTAL_PT(int n, const scalar* Tensor_1458, const scalar* Tensor_1459, const scalar* Tensor_1460, const scalar* Tensor_14, const scalar* Tensor_15, const scalar* Tensor_5, scalar* Tensor_1462, scalar* Tensor_1468, scalar* Tensor_1472);
void Function_CBC_TOTAL_PT(int , const scalar*, const scalar*, const scalar*, const scalar*, scalar*, scalar*, scalar*);
void Function_CBC_TOTAL_PT_grad(int n, const scalar* Tensor_1458, const scalar* Tensor_1459, const scalar* Tensor_1460, const scalar* Tensor_14, const scalar* Tensor_15, const scalar* Tensor_5, const scalar* Tensor_1473, const scalar* Tensor_1474, const scalar* Tensor_1475, scalar* Tensor_1476, scalar* Tensor_1477, scalar* Tensor_1478, scalar* Tensor_1479, scalar* Tensor_1480, scalar* Tensor_1481);
scalar objective(const mat& U, const vec& T, const vec& p);
void objective_grad(const mat& U, const vec& T, const vec& p, mat& Ua, vec& Ta, vec& pa);

#endif